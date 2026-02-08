import unittest

from vanning.geometry import BoxPlacement, Container, boxes_collide, is_inside_container, oriented_size


class GeometryStep0Tests(unittest.TestCase):
    def test_collision_face_touch_is_not_collision(self) -> None:
        box1 = BoxPlacement(x=0, y=0, z=0, l=2, w=2, h=2)
        box2 = BoxPlacement(x=2, y=0, z=0, l=2, w=2, h=2)
        self.assertFalse(boxes_collide(box1, box2))

    def test_collision_overlap_is_collision(self) -> None:
        box1 = BoxPlacement(x=0, y=0, z=0, l=2, w=2, h=2)
        box2 = BoxPlacement(x=1.5, y=0, z=0, l=2, w=2, h=2)
        self.assertTrue(boxes_collide(box1, box2))

    def test_collision_separated_is_not_collision(self) -> None:
        box1 = BoxPlacement(x=0, y=0, z=0, l=2, w=2, h=2)
        box2 = BoxPlacement(x=3, y=0, z=0, l=2, w=2, h=2)
        self.assertFalse(boxes_collide(box1, box2))

    def test_inside_container_boundary_ok(self) -> None:
        container = Container(l=10, w=8, h=6)
        box = BoxPlacement(x=8, y=6, z=4, l=2, w=2, h=2)
        self.assertTrue(is_inside_container(box, container))

    def test_inside_container_out_of_bounds_ng(self) -> None:
        container = Container(l=10, w=8, h=6)
        box = BoxPlacement(x=8, y=6, z=4, l=3, w=2, h=2)
        self.assertFalse(is_inside_container(box, container))

    def test_oriented_size(self) -> None:
        self.assertEqual(oriented_size(1400, 1000, 800, 0), (1400, 1000, 800))
        self.assertEqual(oriented_size(1400, 1000, 800, 90), (1000, 1400, 800))

    def test_oriented_size_invalid_rotation(self) -> None:
        with self.assertRaises(ValueError):
            oriented_size(1400, 1000, 800, 45)


if __name__ == "__main__":
    unittest.main()

