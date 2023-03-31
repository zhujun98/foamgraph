import pytest

import math

import numpy as np

from foamgraph.utility import (
    array_to_log_scale, normalize_angle, parse_boundary, parse_id,
    parse_slice, parse_slice_inv
)


def test_parserboundary():
    invalid_inputs = ["1., 2., 3.0", "1, ", ", 2", "a a", ", 1,,2, ",
                      "2.0, 0.1", "1, 1"]
    for v in invalid_inputs:
        with pytest.raises(ValueError):
            parse_boundary(v)

    assert parse_boundary("0.1, 2") == (0.1, 2)
    assert parse_boundary(" 0.1, 2.0 ") == (0.1, 2)

    # test parse -Inf and Inf
    assert parse_boundary(" -inf, inf ") == (-np.inf, np.inf)
    lb, ub = parse_boundary(" -Inf, 0 ")
    assert math.isinf(lb)
    assert math.isfinite(ub)
    lb, ub = parse_boundary(" -100, INF ")
    assert math.isfinite(lb)
    assert math.isinf(ub)


def test_parseids():
    assert parse_id(":") == [-1]
    assert parse_id("  : ") == [-1]
    assert parse_id("  ") == []
    assert parse_id("1, 2, 3") == [1, 2, 3]
    assert parse_id("1, 2, ,3") == [1, 2, 3]
    assert parse_id("1, 1, ,1") == [1]

    # self.assertEqual([1, 2], parse_id("1:3"))
    # self.assertEqual([1, 2, 5], parse_id("1:3, 5"))
    # self.assertEqual([1, 2, 5], parse_id("1:3, , 5"))
    # self.assertEqual([1, 2, 5], parse_id(" 1 : 3 , , 5"))
    # self.assertEqual([1, 2, 5], parse_id(",, 1 : 3 , , 5,, "))
    # self.assertEqual([1, 2, 5], parse_id("1:3, 5"))
    # self.assertEqual([0, 1, 2, 5, 6, 7], parse_id("0:3, 5, 6:8"))
    # self.assertEqual([0, 1, 2, 3, 4], parse_id("0:3, 1:5"))
    # self.assertEqual([0, 1, 2, 3, 4], parse_id("0:3, 1:5"))
    # self.assertEqual([], parse_id("4:4"))
    # self.assertEqual([0, 2, 4, 6, 8], parse_id("0:10:2"))

    invalid_inputs = ["1, 2, ,a", "1:", ":1", "-1:3", "2:a", "a:b",
                      "1:2:3:4", "4:1:-1"]
    for v in invalid_inputs:
        with pytest.raises(ValueError):
            parse_id(v)


def test_parseslice():
    with pytest.raises(ValueError):
        parse_slice("")

    with pytest.raises(ValueError):
        parse_slice(":::")

    with pytest.raises(ValueError):
        parse_slice("1:5:2:1")

    # self.assertListEqual([None, 2], parse_slice('2'))
    # self.assertListEqual([None, 2], parse_slice(':2'))
    # self.assertListEqual([2, 3], parse_slice('2:3'))
    # self.assertListEqual([-3, -1], parse_slice('-3:-1'))
    # self.assertListEqual([None, None], parse_slice(":"))
    # self.assertListEqual([2, None], parse_slice("2:"))
    # self.assertListEqual([None, 3], parse_slice(':3'))
    # self.assertListEqual([1, 4, 2], parse_slice('1:4:2'))
    # # input with space in between
    # self.assertListEqual([1, 4, 2], parse_slice(' 1 :  4 : 2   '))
    # self.assertListEqual([1, -4, 2], parse_slice('1:-4:2'))
    # self.assertListEqual([2, None, 4], parse_slice('2::4'))
    # self.assertListEqual([1, 3, None], parse_slice('1:3:'))
    # self.assertListEqual([None, None, 4], parse_slice('::4'))
    # self.assertListEqual([2, None, None], parse_slice('2::'))
    # self.assertListEqual([None, None, None], parse_slice('::'))

    with pytest.raises(ValueError):
        parse_slice('2.0')

    with pytest.raises(ValueError):
        parse_slice('2:3.0:2.0')


def test_parse_slice_inv():
    with pytest.raises(ValueError):
        parse_slice_inv("")

    with pytest.raises(ValueError):
        parse_slice_inv(":::")

    with pytest.raises(ValueError):
        parse_slice_inv("1:a")

    for s in [':2', '2:3', '-3:-1', ":", "2:", ':3', '1:4:2',
              '1:-4:2', '2::4', '1:3:', '::4', '2::', '::']:
        assert parse_slice_inv(str(parse_slice(s))) == s


def test_normalize_angle():
    assert normalize_angle(361) == 1
    assert normalize_angle(-720) == 0
    assert normalize_angle(540) == 180
    assert normalize_angle(181) == -179


def test_array_to_log_scale():
    arr = np.array([0, 1, 10], dtype=np.int64)
    ret = array_to_log_scale(arr)
    np.testing.assert_array_equal(ret, [0, 0, 1])
    assert ret.dtype == np.float64
    np.testing.assert_array_equal(arr, [0, 1, 10])

    arr = np.array([0, 1, 10], dtype=np.int64)
    array_to_log_scale(arr, inplace=True)
    np.testing.assert_array_equal(arr, [0, 1, 10])  # inplace ignored for integer type

    arr = np.array([0, 1, 10], dtype=np.float32)
    ret = array_to_log_scale(arr)
    np.testing.assert_array_equal(ret, [-1, 0, 1])
    np.testing.assert_array_equal(arr, [0, 1, 10])
    assert ret.dtype == np.float32

    arr = np.array([0, 1, 10], dtype=np.float32)
    array_to_log_scale(arr, inplace=True)
    np.testing.assert_array_equal(arr, [-1, -0, 1])

    arr = np.array([-1e-8, 0, 1e-8, 1e-4, 10], dtype=np.float32)
    ret = array_to_log_scale(arr)
    np.testing.assert_array_almost_equal(ret, [-9, -9, -8, -4, 1])
