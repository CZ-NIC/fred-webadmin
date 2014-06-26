from .base import enable_corba_comparison, revert_to_default_corba_comparison, enable_corba_comparison_decorator
from fred_webadmin.corba import Registry, ccReg


class TestCorbaComparison(object):
    def test_corba_comaprison_not_working(self):
        assert ccReg.DateType(1, 1, 2000) != ccReg.DateType(1, 1, 2000)

    def test_corba_enabling_comparison(self):
        assert ccReg.DateType(1, 1, 2000) != ccReg.DateType(1, 1, 2000)
        enable_corba_comparison(ccReg.DateType)
        assert ccReg.DateType(1, 1, 2000) == ccReg.DateType(1, 1, 2000)
        assert ccReg.DateType(1, 1, 2000) != ccReg.DateType(2, 1, 2000)
        revert_to_default_corba_comparison(ccReg.DateType)
        assert ccReg.DateType(1, 1, 2000) != ccReg.DateType(1, 1, 2000)

    @enable_corba_comparison_decorator(ccReg.DateType)
    def test_corba_comaprison_decorator(self):
        assert ccReg.DateType(1, 1, 2000) == ccReg.DateType(1, 1, 2000)
