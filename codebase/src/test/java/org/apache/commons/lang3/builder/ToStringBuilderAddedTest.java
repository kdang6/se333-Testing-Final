package org.apache.commons.lang3.builder;

import org.junit.Test;
import static org.junit.Assert.*;

public class ToStringBuilderAddedTest {

    @Test
    public void appendFieldsProduceExpectedContent() {
        ToStringBuilder tb = new ToStringBuilder(this, ToStringStyle.SHORT_PREFIX_STYLE);
        tb.append("age", 30);
        tb.append("name", "Kenny");
        String s = tb.toString();
        assertTrue(s.contains("age=30") || s.contains("age= 30") || s.contains("age:30"));
        assertTrue(s.contains("name=Kenny") || s.contains("name:Kenny") || s.contains("name= Kenny"));
    }

    @Test
    public void appendArrayIncludesElements() {
        ToStringBuilder tb = new ToStringBuilder(this, ToStringStyle.DEFAULT_STYLE);
        tb.append("arr", new int[]{1,2,3});
        String s = tb.toString();
        assertTrue(s.contains("1") && s.contains("2") && s.contains("3"));
    }

}
