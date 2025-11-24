package entity.connection.response;

import com.google.gson.annotations.SerializedName;

public class MoveResponse {
    @SerializedName("agent_index")
    private int agentId;
    private String response;

    public MoveResponse(int agentId, String response) {
        this.agentId = agentId;
        this.response = response;
    }

    public int getAgentId() {
        return this.agentId;
    }

    public String getResponse() {
        return this.response;
    }
}