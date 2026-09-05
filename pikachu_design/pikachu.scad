// =====================================================================
// Mini Pikachu Figurine (~30mm / 3cm) - 3D Printable Figurine
// =====================================================================

$fa = $preview ? 12 : 8;
$fs = $preview ? 0.8 : 0.4;

module pikachu() {
    union() {
        // --- 1. Chubby Body (Plump rounded pear) ---
        hull() {
            translate([0, 0, 6.5]) scale([1.05, 0.98, 0.9]) sphere(r=6.8);
            translate([0, -0.4, 11.5]) scale([0.96, 0.92, 0.95]) sphere(r=5.8);
        }

        // --- 2. Chubby Head with Puffy Cheeks ---
        hull() {
            translate([0, 0, 16.8]) sphere(r=6.2);
            translate([3.8, -1.8, 15.0]) sphere(r=2.8);
            translate([-3.8, -1.8, 15.0]) sphere(r=2.8);
        }

        // --- 3. Classic Pointed Ears ---
        for (s = [-1, 1]) {
            translate([s * 3.4, 0.0, 21.5])
                rotate([-5, s * 34, -s * 8])
                    hull() {
                        sphere(r=2.0);
                        translate([0, 0, 4.5]) sphere(r=1.5);
                        translate([0, 0, 9.5]) sphere(r=0.4);
                    }
        }

        // --- 4. Little Stubby Arms reaching forward on Belly ---
        for (s = [-1, 1]) {
            hull() {
                translate([s * 4.2, -0.8, 11.2]) sphere(r=1.8);
                translate([s * 1.4, -5.4, 9.5]) sphere(r=1.4);
            }
        }

        // --- 5. Chubby Feet at Base ---
        for (s = [-1, 1]) {
            hull() {
                translate([s * 3.6, -1.2, 1.8]) scale([1.1, 1.4, 0.8]) sphere(r=2.2);
                translate([s * 3.4, -4.5, 1.2]) scale([1.0, 1.3, 0.7]) sphere(r=1.8);
            }
        }

        // --- 6. Iconic Lightning Tail ---
        translate([0, 4.0, 4.0])
            rotate([32, 0, 0])
                linear_extrude(height=1.8, center=true)
                    polygon(points=[
                        [0, 0], [1.5, 0], [1.2, 3.8], [3.2, 3.3], [2.5, 7.0],
                        [4.5, 6.5], [3.5, 12.5], [-0.8, 15.0], [0.3, 10.5],
                        [-1.2, 11.0], [0, 6.0], [-1.8, 6.5], [-0.3, 3.0], [-1.2, 3.0], [-0.3, 0]
                    ]);
        // Tail anchor solid connection
        hull() {
            translate([0, 3.2, 4.5]) sphere(r=2.4);
            translate([0, 4.5, 5.5]) sphere(r=1.6);
        }

        // --- 7. Embossed Face Details (Clear on 3D print) ---
        // Big round Eyes
        for (s = [-1, 1]) {
            translate([s * 2.8, -5.6, 17.5])
                rotate([-14, s * 16, 0])
                    scale([1.0, 0.6, 1.15])
                        sphere(r=1.2);
        }

        // Tiny Nose
        translate([0, -6.3, 16.3])
            scale([1.2, 0.8, 0.8])
                sphere(r=0.45);

        // Rosy Cheeks (Pikachu electric pouches)
        for (s = [-1, 1]) {
            translate([s * 4.6, -4.2, 14.8])
                scale([1.0, 0.8, 1.0])
                    sphere(r=1.6);
        }

        // Open Smile
        translate([0, -5.9, 15.2])
            rotate([15, 0, 0])
                hull() {
                    translate([-1.1, 0, 0]) sphere(r=0.35);
                    translate([0, -0.2, -0.3]) sphere(r=0.42);
                    translate([1.1, 0, 0]) sphere(r=0.35);
                }
    }
}

// Flat build base for perfect FDM/Resin bed adhesion
difference() {
    translate([0, 0, -0.2])
        pikachu();
    translate([0, 0, -10.0])
        cube([50, 50, 20], center=true);
}
