package org.apache.commons.lang3.reflect;

import org.junit.Test;
import static org.junit.Assert.*;

public class TypeUtilsAddedTest {

    @Test
    public void isAssignable_ClassToClass() {
        // Integer is assignable to Number
        assertTrue(TypeUtils.isAssignable(Integer.class, Number.class));
        // null types are assignable to non-primitive types
        assertTrue(TypeUtils.isAssignable(null, Integer.class));
        // Integer class is not assignable to primitive int
        assertFalse(TypeUtils.isAssignable(Integer.class, int.class));
    }

}
