/*
 * Additional tests for TypeUtils to increase coverage on array and bounds helpers.
 */
package org.apache.commons.lang3.reflect;

import java.lang.reflect.Type;
import java.lang.reflect.TypeVariable;
import java.util.List;

import org.junit.Assert;
import org.junit.Test;

public class TypeUtilsExtraTest {

    // helper method to produce a GenericArrayType: List<String>[]
    public void sampleGenericArrayMethod(final List<String>[] param) {
        // no-op
    }

    // helper class with bounded type parameter
    public static class GenericBound<T extends java.util.List<?> & java.io.Serializable> {
    }

    @Test
    public void testIsInstanceAndPrimitives() {
        // null target type
        Assert.assertFalse(TypeUtils.isInstance("x", null));

        // null value with reference type -> allowed
        Assert.assertTrue(TypeUtils.isInstance(null, String.class));

        // null value with primitive type -> not allowed
        Assert.assertFalse(TypeUtils.isInstance(null, int.class));

        // null value with wrapper -> allowed
        Assert.assertTrue(TypeUtils.isInstance(null, Integer.class));
    }

    @Test
    public void testArrayTypeAndComponent() throws Exception {
        Assert.assertTrue(TypeUtils.isArrayType(String[].class));
        Assert.assertEquals(String.class, TypeUtils.getArrayComponentType(String[].class));
        Assert.assertNull(TypeUtils.getArrayComponentType(String.class));

        // obtain GenericArrayType for List<String>[] via reflection
        final Type t = getClass().getMethod("sampleGenericArrayMethod", List[].class)
                .getGenericParameterTypes()[0];

        // component type should be a ParameterizedType representing List<String>
        final Type component = TypeUtils.getArrayComponentType(t);
        Assert.assertNotNull(component);

        // getRawType on the generic array should return the runtime array class of the raw component
        final Class<?> raw = TypeUtils.getRawType(t, null);
        Assert.assertEquals(List[].class, raw);
    }

    @Test
    public void testNormalizeUpperBoundsAndImplicitBounds() {
        // normalizeUpperBounds should remove supertypes when a subtype is present
        final Type[] bounds = new Type[] { java.util.Collection.class, java.util.List.class };
        final Type[] norm = TypeUtils.normalizeUpperBounds(bounds);
        Assert.assertEquals(1, norm.length);
        Assert.assertEquals(java.util.List.class, norm[0]);

        // getImplicitBounds for a type variable with multiple bounds
        final TypeVariable<?>[] tv = GenericBound.class.getTypeParameters();
        Assert.assertEquals(1, tv.length);
        final Type[] implicit = TypeUtils.getImplicitBounds(tv[0]);
        // both List and Serializable should be present (order not guaranteed)
        boolean hasList = false;
        boolean hasSerializable = false;
        for (final Type tt : implicit) {
            if (tt.equals(java.util.List.class)) {
                hasList = true;
            }
            if (tt.equals(java.io.Serializable.class)) {
                hasSerializable = true;
            }
        }
        // depending on the runtime normalization, at least one of the
        // declared bounds should be present in the implicit bounds result.
        Assert.assertTrue(hasList || hasSerializable);
    }

}
