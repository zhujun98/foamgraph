import pytest

from foamgraph import GraphView

from foamgraph.test import visualize


@pytest.fixture(scope="function")
def view():
    graph_view = GraphView()
    if visualize():
        graph_view.show()
    return graph_view
