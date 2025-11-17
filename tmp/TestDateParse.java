import java.text.SimpleDateFormat;
import java.text.ParsePosition;
import java.text.ParseException;
import java.util.Locale;
import java.util.Date;

public class TestDateParse {
    public static void main(String[] args) throws Exception {
        Locale.setDefault(Locale.GERMAN);
        SimpleDateFormat sdf = new SimpleDateFormat("EEE, dd MMM yyyy HH:mm:ss zzz", Locale.GERMAN);
        String s = "Mi, 09 Apr 2008 23:55:38 GMT";
        System.out.println("Parser created for German locale");
        System.out.println("ShortWeekdays: ");
        for (String wd: sdf.getDateFormatSymbols().getShortWeekdays()) System.out.println("wd='"+wd+"'");
        System.out.println("ShortMonths: ");
        for (String m: sdf.getDateFormatSymbols().getShortMonths()) System.out.println("m='"+m+"'");
        try {
            Date d = sdf.parse(s);
            System.out.println("Parsed: " + d);
        } catch (ParseException e) {
            System.out.println("ParseException: " + e.getMessage());
        }
        // try with dot added
        try {
            Date d = sdf.parse("Mi, 09 Apr. 2008 23:55:38 GMT");
            System.out.println("Parsed with dot: " + d);
        } catch (ParseException e) {
            System.out.println("ParseException with dot: " + e.getMessage());
        }
            // Try parsing without weekday
            try {
                SimpleDateFormat sdf2 = new SimpleDateFormat("dd MMM yyyy HH:mm:ss zzz", Locale.GERMAN);
                Date d = sdf2.parse("09 Apr 2008 23:55:38 GMT");
                System.out.println("Parsed without weekday: " + d);
            } catch (ParseException e) {
                System.out.println("ParseException without weekday: " + e.getMessage());
            }
            try {
                SimpleDateFormat sdf3 = new SimpleDateFormat("dd MMM yyyy HH:mm:ss", Locale.GERMAN);
                Date d = sdf3.parse("09 Apr 2008 23:55:38");
                System.out.println("Parsed without weekday/tz: " + d);
            } catch (ParseException e) {
                System.out.println("ParseException without weekday/tz: " + e.getMessage());
            }
    }
}
