package org.apache.commons.lang3.builder;

import static org.junit.Assert.*;

import org.junit.Test;

public class BuilderTest {

    @Test
    public void testSimpleBuilder() {
        Builder<String> b = new Builder<String>() {
            @Override
            public String build() {
                return "ok";
            }
        };
        assertEquals("ok", b.build());
    }
}
