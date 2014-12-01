import os, sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from navigation import NavigationExtractor

def test_join():
    def eq(a, b):
        assert a == b

    fixtures = (
([0, 0, 0, 0, 0, 0, 0, 0], [0, 1, 0],     [0, 0, 0, 0, 0, 0, 1, 0]),
([0, 0, 0, 0, 0, 0, 1, 0], [1, 0],        [0, 0, 0, 0, 0, 0, 2, 0]),
([0, 0, 0, 0, 0, 0, 0, 0], [1, 0],        [0, 0, 0, 0, 0, 0, 1, 0]),
([0, 0, 0, 0, 0, 0, 1, 0], [11, 0, 1, 0], [0, 0, 0, 0, 11, 0, 2, 0]),
([0, 0, 0, 0, 0, 0, 2, 0], [1, 0],        [0, 0, 0, 0, 0, 0, 3, 0]),
            )
    
    ne = NavigationExtractor()
    for a, b, c in fixtures:
        yield eq, ne.join_tags(a, b), c
