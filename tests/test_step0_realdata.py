import unittest

from vanning.geometry import boxes_collide, is_inside_container
from vanning.problem_spec import BOX_DIMS, CONTAINER_20FT, box_size, place_box


class Step0RealDataTests(unittest.TestCase):
    def test_problem_constants(self) -> None:
        self.assertEqual((CONTAINER_20FT.l, CONTAINER_20FT.w, CONTAINER_20FT.h), (5898, 2352, 2393))
        self.assertEqual(BOX_DIMS["A"], (1400, 1000, 800))
        self.assertEqual(BOX_DIMS["B"], (1200, 900, 700))
        self.assertEqual(BOX_DIMS["C"], (800, 600, 600))

    def test_orientation_on_real_box_a(self) -> None:
        self.assertEqual(box_size("A", 0), (1400, 1000, 800))
        self.assertEqual(box_size("A", 90), (1000, 1400, 800))

    def test_inside_container_boundary_ok_with_90deg_rotation(self) -> None:
        # A box at exact max boundary with 90deg orientation should still be valid.
        box = place_box("A", x=5898 - 1000, y=2352 - 1400, z=2393 - 800, yaw_deg=90)
        self.assertTrue(is_inside_container(box, CONTAINER_20FT))

    def test_inside_container_out_of_bounds_ng(self) -> None:
        # Move 1mm outside the x limit.
        box = place_box("A", x=5898 - 1000 + 1, y=2352 - 1400, z=2393 - 800, yaw_deg=90)
        self.assertFalse(is_inside_container(box, CONTAINER_20FT))

    def test_face_touch_is_not_collision_on_real_sizes(self) -> None:
        box_a = place_box("A", x=0, y=0, z=0, yaw_deg=0)
        box_c = place_box("C", x=1400, y=0, z=0, yaw_deg=0)  # Touches A on x face only.
        self.assertFalse(boxes_collide(box_a, box_c))

    def test_internal_overlap_is_collision_on_real_sizes(self) -> None:
        box_a = place_box("A", x=0, y=0, z=0, yaw_deg=0)
        box_c = place_box("C", x=1300, y=0, z=0, yaw_deg=0)  # 100mm overlap in x.
        self.assertTrue(boxes_collide(box_a, box_c))

    def test_three_boxes_inside_and_pairwise_non_collision(self) -> None:
        # A small feasible layout sample using actual dimensions.
        boxes = [
            place_box("A", x=0, y=0, z=0, yaw_deg=0),
            place_box("B", x=1400, y=0, z=0, yaw_deg=0),
            place_box("C", x=2600, y=0, z=0, yaw_deg=0),
        ]
        for box in boxes:
            self.assertTrue(is_inside_container(box, CONTAINER_20FT))

        for i in range(len(boxes)):
            for j in range(i + 1, len(boxes)):
                self.assertFalse(boxes_collide(boxes[i], boxes[j]))


if __name__ == "__main__":
    unittest.main()

