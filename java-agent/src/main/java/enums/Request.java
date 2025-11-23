package enums;

import data.gson.Distance;
import interpreter.Interpreter;
import java.util.function.Function;

public enum Request {

    DISTANCE_REQUEST(
        "distance",
        Integer.class,
        (json) -> Interpreter.GSON.fromJson(json, Distance.class).getDistance()
    );

    private final String identifier;
    private final Class<?> typeClass;
    private final Function<String, Object> conversion;

    <T> Request(String identifier, Class<T> typeClass, Function<String, Object> conversion) {
        this.identifier = identifier;
        this.typeClass = typeClass;
        this.conversion = conversion;
    }

    public String getIdentifier() {
        return this.identifier;
    }

    public <T> T getConversion(String value) {
        final Object converted = this.conversion.apply(value);
        return (T) this.typeClass.cast(converted);
    }
}