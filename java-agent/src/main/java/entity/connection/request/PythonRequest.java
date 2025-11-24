package entity.connection.request;

import com.google.gson.annotations.SerializedName;

public class PythonRequest {
    @SerializedName("agent_index")
    private int agentId;
    private Object value;

    public PythonRequest(int agentId, Object value) {
        this.agentId = agentId;
        this.value = value;
    }

    public int getAgentId() {
        return this.agentId;
    }

    public Object getValue() {
        return this.value;
    }
}