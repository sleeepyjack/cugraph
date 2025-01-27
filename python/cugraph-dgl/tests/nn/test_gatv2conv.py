# Copyright (c) 2023, NVIDIA CORPORATION.
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import pytest

from cugraph_dgl.nn.conv.base import SparseGraph
from cugraph_dgl.nn import GATv2Conv as CuGraphGATv2Conv
from .common import create_graph1

dgl = pytest.importorskip("dgl", reason="DGL not available")
torch = pytest.importorskip("torch", reason="PyTorch not available")

ATOL = 1e-6


@pytest.mark.parametrize("bipartite", [False, True])
@pytest.mark.parametrize("idtype_int", [False, True])
@pytest.mark.parametrize("max_in_degree", [None, 8])
@pytest.mark.parametrize("num_heads", [1, 2, 7])
@pytest.mark.parametrize("residual", [False, True])
@pytest.mark.parametrize("to_block", [False, True])
@pytest.mark.parametrize("sparse_format", ["coo", "csc", None])
def test_gatv2conv_equality(
    bipartite, idtype_int, max_in_degree, num_heads, residual, to_block, sparse_format
):
    from dgl.nn.pytorch import GATv2Conv

    torch.manual_seed(12345)
    g = create_graph1().to("cuda")

    if idtype_int:
        g = g.int()
    if to_block:
        g = dgl.to_block(g)

    size = (g.num_src_nodes(), g.num_dst_nodes())

    if bipartite:
        in_feats = (10, 3)
        nfeat = (
            torch.rand(g.num_src_nodes(), in_feats[0]).cuda(),
            torch.rand(g.num_dst_nodes(), in_feats[1]).cuda(),
        )
    else:
        in_feats = 10
        nfeat = torch.rand(g.num_src_nodes(), in_feats).cuda()
    out_feats = 2

    if sparse_format == "coo":
        sg = SparseGraph(
            size=size, src_ids=g.edges()[0], dst_ids=g.edges()[1], formats="csc"
        )
    elif sparse_format == "csc":
        offsets, indices, _ = g.adj_tensors("csc")
        sg = SparseGraph(size=size, src_ids=indices, cdst_ids=offsets, formats="csc")

    args = (in_feats, out_feats, num_heads)
    kwargs = {"bias": False, "allow_zero_in_degree": True}

    conv1 = GATv2Conv(*args, **kwargs).cuda()
    out1 = conv1(g, nfeat)

    conv2 = CuGraphGATv2Conv(*args, **kwargs).cuda()
    with torch.no_grad():
        conv2.attn.data = conv1.attn.data.flatten()
        conv2.lin_src.weight.data = conv1.fc_src.weight.data.detach().clone()
        conv2.lin_dst.weight.data = conv1.fc_dst.weight.data.detach().clone()
        if residual and conv2.residual:
            conv2.lin_res.weight.data = conv1.fc_res.weight.data.detach().clone()

    if sparse_format is not None:
        out2 = conv2(sg, nfeat, max_in_degree=max_in_degree)
    else:
        out2 = conv2(g, nfeat, max_in_degree=max_in_degree)

    assert torch.allclose(out1, out2, atol=ATOL)

    grad_out1 = torch.rand_like(out1)
    grad_out2 = grad_out1.clone().detach()
    out1.backward(grad_out1)
    out2.backward(grad_out2)

    assert torch.allclose(
        conv1.fc_src.weight.grad, conv2.lin_src.weight.grad, atol=ATOL
    )
    assert torch.allclose(
        conv1.fc_dst.weight.grad, conv2.lin_dst.weight.grad, atol=ATOL
    )

    assert torch.allclose(conv1.attn.grad, conv1.attn.grad, atol=ATOL)


@pytest.mark.parametrize("bias", [False, True])
@pytest.mark.parametrize("bipartite", [False, True])
@pytest.mark.parametrize("concat", [False, True])
@pytest.mark.parametrize("max_in_degree", [None, 8, 800])
@pytest.mark.parametrize("num_heads", [1, 2, 7])
@pytest.mark.parametrize("to_block", [False, True])
@pytest.mark.parametrize("use_edge_feats", [False, True])
def test_gatv2conv_edge_feats(
    bias, bipartite, concat, max_in_degree, num_heads, to_block, use_edge_feats
):
    torch.manual_seed(12345)
    g = create_graph1().to("cuda")

    if to_block:
        g = dgl.to_block(g)

    if bipartite:
        in_feats = (10, 3)
        nfeat = (
            torch.rand(g.num_src_nodes(), in_feats[0]).cuda(),
            torch.rand(g.num_dst_nodes(), in_feats[1]).cuda(),
        )
    else:
        in_feats = 10
        nfeat = torch.rand(g.num_src_nodes(), in_feats).cuda()
    out_feats = 2

    if use_edge_feats:
        edge_feats = 3
        efeat = torch.rand(g.num_edges(), edge_feats).cuda()
    else:
        edge_feats = None
        efeat = None

    conv = CuGraphGATv2Conv(
        in_feats,
        out_feats,
        num_heads,
        concat=concat,
        edge_feats=edge_feats,
        bias=bias,
        allow_zero_in_degree=True,
    ).cuda()
    out = conv(g, nfeat, efeat=efeat, max_in_degree=max_in_degree)

    grad_out = torch.rand_like(out)
    out.backward(grad_out)
