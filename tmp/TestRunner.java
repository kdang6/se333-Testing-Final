public class TestRunner {
    public static void main(String[] args) {
        try {
            java.lang.Number n = org.apache.commons.lang3.math.NumberUtils.createNumber("0x7FFFFFFF");
            System.out.println(n.getClass().getName() + ": " + n);
        } catch (Exception ex) {
            ex.printStackTrace();
        }
    }
}
