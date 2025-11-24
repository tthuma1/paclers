package interpreter;

import com.google.gson.Gson;
import com.sun.net.httpserver.HttpExchange;
import com.sun.net.httpserver.HttpServer;
import data.GameData;
import entity.connection.request.PythonRequest;
import entity.connection.response.MoveResponse;
import entity.Position;
import enums.Direction;
import enums.GameState;
import enums.Request;
import java.io.BufferedReader;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.InetSocketAddress;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

public class Interpreter {
    private final Map<Integer, GameInterpreter> agents = new ConcurrentHashMap<>();
    private final Map<Request, URL> endpoints = new ConcurrentHashMap<>();

    public static final Gson GSON = new Gson();
    private static final String BASE_URL = "http://127.0.0.1:5001/%s"; // Flask listening on 5001

    public Interpreter() throws Exception {
        final HttpServer server = HttpServer.create(new InetSocketAddress(8080), 0);
        server.createContext("/choose_action", this::handleMove);
        server.setExecutor(null);
        server.start();

        for (final Request request : Request.values()) {
            final URL url = new URL(BASE_URL.formatted(request.getIdentifier()));
            this.endpoints.put(request, url);
        }

        this.agents.put(0, new GameInterpreter(this, 0, GameState.FINDING_FOOD));
        this.agents.put(1, new GameInterpreter(this, 1, GameState.DEFENDING));
        System.out.println("Java Agent Server running on port 8080...");
    }

    private void handleMove(HttpExchange exchange) {
        try {
            if (!this.handleRequest(exchange)) {
                return;
            }

            try (InputStream body = exchange.getRequestBody()) {
                final String requestJson = new String(body.readAllBytes(), StandardCharsets.UTF_8);
                final GameData gameData = GSON.fromJson(requestJson, GameData.class);
                final GameInterpreter interpreter = this.agents.get(gameData.getAgentIndex());

                final Direction response = interpreter.handleMove(gameData);
                final Position current = gameData.getAgentPosition();

                //System.out.println("Move: " + response + " (current=" + current + ", next=" + response.applyModifier(current) + ")");
                this.sendResponse(exchange, GSON.toJson(new MoveResponse(gameData.getAgentIndex(), response.toString())));
            }
        } catch (Exception e) {
            e.printStackTrace();
        }
    }

    private void sendResponse(HttpExchange exchange, String gson) {
        try (exchange) {
            final byte[] bytes = gson.getBytes(StandardCharsets.UTF_8);
            exchange.sendResponseHeaders(200, 0);

            try (final OutputStream os = exchange.getResponseBody()) {
                os.write(bytes);
            }
        } catch (Exception e) {
            System.out.println("Failed to respond for gson: " + gson);
            e.printStackTrace();
        }
    }

    private boolean handleRequest(HttpExchange exchange) throws Exception {
        if (!exchange.getRequestMethod().equalsIgnoreCase("POST")) {
            String msg = "Server is running.";
            exchange.sendResponseHeaders(200, msg.length());
            exchange.getResponseBody().write(msg.getBytes());
            exchange.close();
            return false;
        }

        return true;
    }

    public <T> T callPython(int agentId, Request request, Object payload) {
        try {
            final HttpURLConnection connection = this.createConnection(request);
            final PythonRequest pythonRequest = new PythonRequest(agentId, payload);
            final String json = GSON.toJson(pythonRequest);

            try (OutputStream os = connection.getOutputStream()) {
                os.write(json.getBytes(StandardCharsets.UTF_8));
                os.flush();
            }

            int code = connection.getResponseCode();
            if (code != HttpURLConnection.HTTP_OK) {
                throw new RuntimeException("Python returned HTTP " + code);
            }

            // Read response
            try (final BufferedReader br = new BufferedReader(new InputStreamReader(connection.getInputStream()))) {
                final StringBuilder builder = new StringBuilder();
                String line;
                while ((line = br.readLine()) != null) {
                    builder.append(line);
                }

                return request.getConversion(builder.toString());
            }
        } catch (Exception e) {
            e.printStackTrace();
            return null;
        }
    }

    private HttpURLConnection createConnection(Request request) {
        final URL url = this.endpoints.get(request);

        try {
            final HttpURLConnection connection = (HttpURLConnection) url.openConnection();
            connection.setRequestMethod("POST");
            connection.setDoOutput(true);
            connection.setRequestProperty("Content-Type", "application/json");
            return connection;
        } catch (Exception e) {
            throw new RuntimeException("Failed to open a connection for url '" + url + "'");
        }
    }
}