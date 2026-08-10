import java.util.ArrayList;
import java.util.List;

/**
 * Evozi string-deobfuscator (HTTP Injector Lite 5.3.1) — proven working 2026-08-10.
 * Decodes the long-constant + 7-blob string table (classes n / b0 / rot).
 *
 * Build:  javac Deobf.java
 * Run:    java Deobf          (needs /opt/work/enc_strings.txt = 7 blobs, one per line)
 *
 * IMPORTANT Java-semantics notes (why Python ports failed):
 *  - ushr-long/ushr-int are LOGICAL shifts
 *  - int-to-short and int-to-long SIGN-EXTEND (negative shorts pollute bits 48-63)
 *  - rot() rotates the sign-extended 32-bit int, then truncates to short
 *  - the per-char helper uses mix16 ONLY (no mix64)
 */
public class Deobf {
    // b0.ﾠ⁮͏(S I)S — rotate on 32-bit sign-extended, truncate to short
    static short rot(short v, int n) {
        int v32 = v;                       // sign-extend to int
        int a = v32 << n;
        int b = v32 >>> (32 - n);          // LOGICAL shift
        return (short) (a | b);
    }

    // b0.ﾠ⁬͏(J)J — 16-bit lane mixer
    static long mix16(long j) {
        short lo_s = (short) (j & 0xFFFF);
        short hi_s = (short) ((j >>> 16) & 0xFFFF);
        short v = (short) (lo_s + hi_s);
        v = rot(v, 9);
        v = (short) (v + lo_s);
        short x1 = (short) (hi_s ^ lo_s);
        short r = rot(lo_s, 13);
        short t = (short) (r ^ x1);
        t = (short) (t ^ (x1 << 5));       // shifts sign-extended 32-bit x1
        short r2 = rot(x1, 10);
        // ALL THREE terms sign-extend to 64-bit (int-to-long) — never mask t with &0xFFFFL
        long out = ((long) v << 32) | ((long) r2 << 16) | ((long) t);
        return out;
    }

    // b0.ﾠ⁫⁫(J)J — splitmix64 finalizer
    static long mix64(long j) {
        long x = j;
        x ^= x >>> 33;
        x *= 7109453100751455733L;
        x ^= x >>> 28;
        x *= -3808689974395783757L;
        x >>>= 32;
        return x;
    }

    // ｎ.ﾠ⁬͏(I [Ljava/lang/String; J)J — per-char helper: mix16 ONLY (no mix64!)
    static long helper(int idx, String[] arr, long j) {
        long x = mix16(j);
        int seg = idx / 8191;
        int pos = idx % 8191;
        long ch = (long) (arr[seg].charAt(pos)) << 32;
        return ch ^ x;
    }

    // ｎ.ﾠ⁮͏(J [Ljava/lang/String;)Ljava/lang/String;
    static String deobf(long j, String[] arr) {
        long v11 = j;
        long v0 = v11 & 0xFFFFFFFFL;
        v0 = mix64(v0);
        v0 = mix16(v0);
        long v3 = (v0 >>> 32) & 0xFFFF;
        v0 = mix16(v0);
        long v7 = (v0 >>> 16) & 0xFFFF0000L;
        v11 >>>= 32;
        v11 ^= v3;
        v11 ^= v7;
        int idx = (int) v11;
        long r = helper(idx, arr, v0);
        long n = (r >>> 32) & 0xFFFF;
        char[] out = new char[(int) n];
        for (int i = 0; i < n; i++) {
            r = helper(idx + i + 1, arr, r);
            long ch = (r >>> 32) & 0xFFFF;
            out[i] = (char) ch;
        }
        return new String(out);
    }

    public static void main(String[] args) throws Exception {
        List<String> enc = new ArrayList<>();
        java.nio.file.Path p = java.nio.file.Paths.get("/opt/work/enc_strings.txt");
        for (String line : java.nio.file.Files.readAllLines(p, java.nio.charset.StandardCharsets.UTF_8)) {
            if (!line.isEmpty()) enc.add(line);
        }
        String[] arr = enc.toArray(new String[0]);
        System.out.println("Loaded " + arr.length + " strings");

        long[] consts = {
            -78612227362228L, -78702421675444L, -78719601544628L, -78801205923252L,
            -77920737627572L, -77937917496756L, -77985162137012L, -78066766515636L,
            -78083946384820L, -78247155142068L, -78272924945844L, -78363119259060L,
            -78156960828852L, -78564982721972L
        };
        for (long c : consts) {
            try {
                System.out.println(c + ": " + deobf(c, arr));
            } catch (Exception e) {
                System.out.println(c + ": ERROR " + e);
            }
        }
    }
}
