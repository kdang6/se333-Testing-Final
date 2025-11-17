package org.apache.commons.lang3.builder;

import org.junit.Test;
import static org.junit.Assert.*;

public class ToStringStyleAddedTest {

    @Test
    public void defaultStyleCanBeChangedAndRestored() {
        ToStringStyle orig = ToStringBuilder.getDefaultStyle();
        ToStringBuilder.setDefaultStyle(ToStringStyle.SIMPLE_STYLE);
        assertEquals(ToStringStyle.SIMPLE_STYLE, ToStringBuilder.getDefaultStyle());
        // restore original style to be polite to other tests
        ToStringBuilder.setDefaultStyle(orig);
    }

}
