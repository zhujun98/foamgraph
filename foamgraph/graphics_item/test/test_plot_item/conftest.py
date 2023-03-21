import pytest

from foamgraph import GraphView

from foamgraph.test import processEvents


@pytest.fixture(scope="function")
def view():
    graph_view = GraphView()
    graph_view.show()
    processEvents()
    return graph_view
