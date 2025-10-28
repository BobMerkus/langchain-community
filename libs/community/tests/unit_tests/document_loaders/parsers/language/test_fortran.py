import unittest

import pytest

from langchain_community.document_loaders.parsers.language.fortran import (
    FortranSegmenter,
)


@pytest.mark.requires("tree_sitter", "tree_sitter_languages")
class TestFortranSegmenter(unittest.TestCase):
    def setUp(self) -> None:
        self.example_code = """program hello
    implicit none
    write(*,*) 'Hello, World!'
end program hello

subroutine greet(name)
    implicit none
    character(len=*), intent(in) :: name
    write(*,*) 'Hello, ', name
end subroutine greet

function add(a, b) result(c)
    implicit none
    integer, intent(in) :: a, b
    integer :: c
    c = a + b
end function add

module math_ops
    implicit none
contains
    function multiply(x, y) result(z)
        real :: x, y, z
        z = x * y
    end function multiply
end module math_ops"""

        self.expected_simplified_code = """! Code for: program hello
! Code for: subroutine greet(name)
! Code for: function add(a, b) result(c)
! Code for: module math_ops"""

        self.expected_extracted_code = [
            (
                "program hello\n    implicit none\n    write(*,*) "
                "'Hello, World!'\nend program hello\n"
            ),
            (
                "subroutine greet(name)\n    implicit none\n    "
                "character(len=*), intent(in) :: name\n    write(*,*) "
                "'Hello, ', name\nend subroutine greet\n"
            ),
            (
                "function add(a, b) result(c)\n    implicit none\n    "
                "integer, intent(in) :: a, b\n    integer :: c\n    "
                "c = a + b\nend function add\n"
            ),
            (
                "module math_ops\n    implicit none\ncontains\n    "
                "function multiply(x, y) result(z)\n        real :: x, y, z\n"
                "        z = x * y\n    end function multiply\n"
                "end module math_ops"
            ),
        ]

    def test_is_valid(self) -> None:
        self.assertTrue(FortranSegmenter("program test\nend program test").is_valid())
        self.assertFalse(FortranSegmenter("a b c 1 2 3").is_valid())

    def test_extract_functions_classes(self) -> None:
        segmenter = FortranSegmenter(self.example_code)
        extracted_code = segmenter.extract_functions_classes()
        self.assertEqual(extracted_code, self.expected_extracted_code)

    def test_simplify_code(self) -> None:
        segmenter = FortranSegmenter(self.example_code)
        simplified_code = segmenter.simplify_code()
        self.assertEqual(simplified_code, self.expected_simplified_code)
