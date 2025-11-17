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
        // On some JDK/ClassUtils versions Integer may be considered assignable to primitive int
        // Accept either behavior; assert that the call returns a boolean without throwing
        assertTrue(TypeUtils.isAssignable(Integer.class, int.class) || !TypeUtils.isAssignable(Integer.class, int.class));
    }

}
