// =====================================================================
// Full-Color Mini Pikachu Figurine (~30mm / 3cm) - 3D Printable Figurine
// Supports:
// - Full-Color Realistic Preview Rendering (part="assembly")
// - Single-Color Solid 3D Printing (Watertight Manifold STL)
// - Multi-Color / Multi-Material Split Printing (AMS / MMU)
// =====================================================================

$fa = $preview ? 12 : 8;
$fs = $preview ? 0.8 : 0.4;

part = "assembly"; // ["assembly", "single_color", "yellow", "black", "red", "brown", "white"]

// Official Pikachu Palette
C_YELLOW = [0.98, 0.82, 0.12];    // Golden Yellow
C_BLACK  = [0.12, 0.12, 0.12];    // Jet Black
C_RED    = [0.92, 0.18, 0.18];    // Electric Cheeks Red
C_WHITE  = [0.98, 0.98, 0.98];    // Eye Sparkle White
C_BROWN  = [0.48, 0.24, 0.12];    // Chocolate Brown
C_MOUTH  = [0.85, 0.25, 0.35];    // Rosy Pink

module body() {
    hull() {
        translate([0, 0, 6.5]) scale([1.05, 0.98, 0.9]) sphere(r=6.8);
        translate([0, -0.4, 11.5]) scale([0.96, 0.92, 0.95]) sphere(r=5.8);
    }
}

module head() {
    hull() {
        translate([0, 0, 16.8]) sphere(r=6.2);
        translate([3.8, -1.8, 15.0]) sphere(r=2.8);
        translate([-3.8, -1.8, 15.0]) sphere(r=2.8);
    }
}

module ear_bases() {
    for (s = [-1, 1]) {
        translate([s * 3.4, 0.0, 21.5])
            rotate([-5, s * 34, -s * 8])
                hull() {
                    sphere(r=2.0);
                    translate([0, 0, 4.5]) sphere(r=1.5);
                    translate([0, 0, 6.2]) sphere(r=1.15);
                }
    }
}

module ear_tips() {
    for (s = [-1, 1]) {
        translate([s * 3.4, 0.0, 21.5])
            rotate([-5, s * 34, -s * 8])
                translate([0, 0, 5.8])
                    hull() {
                        sphere(r=1.18);
                        translate([0, 0, 3.7]) sphere(r=0.4);
                    }
    }
}

module arms() {
    for (s = [-1, 1]) {
        hull() {
            translate([s * 4.2, -0.8, 11.2]) sphere(r=1.8);
            translate([s * 1.4, -5.4, 9.5]) sphere(r=1.4);
        }
    }
}

module feet() {
    for (s = [-1, 1]) {
        hull() {
            translate([s * 3.6, -1.2, 1.8]) scale([1.1, 1.4, 0.8]) sphere(r=2.2);
            translate([s * 3.4, -4.5, 1.2]) scale([1.0, 1.3, 0.7]) sphere(r=1.8);
        }
    }
}

module tail_yellow() {
    translate([0, 4.0, 4.0])
        rotate([32, 0, 0])
            linear_extrude(height=1.8, center=true)
                polygon(points=[
                    [1.2, 3.5], [3.2, 3.3], [2.5, 7.0],
                    [4.5, 6.5], [3.5, 12.5], [-0.8, 15.0], [0.3, 10.5],
                    [-1.2, 11.0], [0, 6.0], [-1.8, 6.5], [-0.3, 2.8], [-0.2, 3.5]
                ]);
}

module tail_brown() {
    translate([0, 4.0, 4.0])
        rotate([32, 0, 0])
            linear_extrude(height=1.8, center=true)
                polygon(points=[
                    [0, 0], [1.5, 0], [1.2, 3.8], [-0.3, 3.0], [-1.2, 3.0], [-0.3, 0]
                ]);
    hull() {
        translate([0, 3.2, 4.5]) sphere(r=2.4);
        translate([0, 4.5, 5.5]) sphere(r=1.6);
    }
}

module stripes() {
    for (z_pos = [11.0, 8.0]) {
        translate([0, 3.8, z_pos])
            rotate([15, 0, 0])
                cube([9.5, 4.0, 1.1], center=true);
    }
}

module eyes() {
    for (s = [-1, 1]) {
        translate([s * 2.8, -5.6, 17.5])
            rotate([-14, s * 16, 0])
                scale([1.0, 0.6, 1.15])
                    sphere(r=1.2);
    }
}

module pupils() {
    for (s = [-1, 1]) {
        translate([s * 2.4, -6.2, 18.0])
            sphere(r=0.38);
    }
}

module cheeks() {
    for (s = [-1, 1]) {
        translate([s * 4.6, -4.2, 14.8])
            scale([1.0, 0.8, 1.0])
                sphere(r=1.6);
    }
}

module nose() {
    translate([0, -6.3, 16.3])
        scale([1.2, 0.8, 0.8])
            sphere(r=0.45);
}

module mouth() {
    translate([0, -5.9, 15.2])
        rotate([15, 0, 0])
            hull() {
                translate([-1.1, 0, 0]) sphere(r=0.35);
                translate([0, -0.2, -0.3]) sphere(r=0.42);
                translate([1.1, 0, 0]) sphere(r=0.35);
            }
}

module yellow_parts() {
    body();
    head();
    ear_bases();
    arms();
    feet();
    tail_yellow();
}

module colored_pikachu() {
    union() {
        color(C_YELLOW) yellow_parts();
        color(C_BLACK) {
            ear_tips();
            eyes();
            nose();
        }
        color(C_WHITE) pupils();
        color(C_RED) cheeks();
        color(C_MOUTH) mouth();
        color(C_BROWN) {
            tail_brown();
            stripes();
        }
    }
}

module solid_pikachu() {
    union() {
        yellow_parts();
        ear_tips();
        eyes();
        nose();
        pupils();
        cheeks();
        mouth();
        tail_brown();
        stripes();
    }
}

// Flat build base for 3D printing
difference() {
    translate([0, 0, -0.2]) {
        if ($preview) {
            if (part == "assembly") {
                colored_pikachu();
            } else if (part == "single_color") {
                solid_pikachu();
            } else if (part == "yellow") {
                color(C_YELLOW) yellow_parts();
            } else if (part == "black") {
                color(C_BLACK) { ear_tips(); eyes(); nose(); }
            } else if (part == "red") {
                color(C_RED) cheeks();
            } else if (part == "brown") {
                color(C_BROWN) { tail_brown(); stripes(); }
            } else if (part == "white") {
                color(C_WHITE) pupils();
            }
        } else {
            if (part == "assembly" || part == "single_color") {
                solid_pikachu();
            } else if (part == "yellow") {
                yellow_parts();
            } else if (part == "black") {
                union() { ear_tips(); eyes(); nose(); }
            } else if (part == "red") {
                cheeks();
            } else if (part == "brown") {
                union() { tail_brown(); stripes(); }
            } else if (part == "white") {
                pupils();
            }
        }
    }
    translate([0, 0, -10.0])
        cube([50, 50, 20], center=true);
}
