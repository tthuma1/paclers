package interpreter;

import com.google.gson.Gson;
import com.sun.net.httpserver.HttpExchange;
import com.sun.net.httpserver.HttpServer;
import data.GameData;
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
    private final GameInterpreter interpreter;
    private final HttpServer server;
    private final Map<Request, URL> endpoints = new ConcurrentHashMap<>();

    public static final Gson GSON = new Gson();
    private static final String BASE_URL = "http://127.0.0.1:5001/%s"; // Flask listening on 5001

    public Interpreter() throws Exception {
        this.server = HttpServer.create(new InetSocketAddress(8080), 0);
        this.server.createContext("/choose_action", this::handleMove);
        this.server.createContext("/get_features", this::handleGetFeatures);
        this.server.setExecutor(null);
        this.server.start();

        for (final Request request : Request.values()) {
            final URL url = new URL(BASE_URL.formatted(request.getIdentifier()));
            this.endpoints.put(request, url);
        }

        this.interpreter = new GameInterpreter(this);
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
                this.sendResponse(exchange, this.interpreter.handleMove(gameData));
            }
        } catch (Exception e) {
            e.printStackTrace();
        }
    }

    private void handleGetFeatures(HttpExchange exchange) {
        try {
            if (!this.handleRequest(exchange)) {
                return;
            }

            try (InputStream body = exchange.getRequestBody()) {
                final String requestJson = new String(body.readAllBytes(), StandardCharsets.UTF_8);
                final GameData gameData = GSON.fromJson(requestJson, GameData.class);
                this.sendResponse(exchange, this.interpreter.handleGetFeatures(gameData));
            }
        } catch (Exception e) {
            e.printStackTrace();
        }
    }

    private void sendResponse(HttpExchange exchange, String gson) {
        try {
            exchange.sendResponseHeaders(200, gson.length());
            OutputStream os = exchange.getResponseBody();
            os.write(gson.getBytes(StandardCharsets.UTF_8));
            os.flush();
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

    public <T> T callPython(Request request, Object payload) {
        try {
            final HttpURLConnection connection = this.createConnection(request);
            final String json = GSON.toJson(payload);

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