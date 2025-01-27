# Copyright (c) 2022-2023, NVIDIA CORPORATION.
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

from pylibcugraph.testing.utils import gen_fixture_params
from cugraph.testing import RAPIDS_DATASET_ROOT_DIR_PATH
from cugraph.datasets import (
    Dataset,
    karate,
    netscience,
    email_Eu_core,
)

# Create Dataset objects from .csv files.
# Once the cugraph.dataset package is updated to include the metadata files for
# these (like karate), these will no longer need to be explicitly instantiated.
hollywood = Dataset(
    csv_file=RAPIDS_DATASET_ROOT_DIR_PATH / "csv/undirected/hollywood.csv",
    csv_col_names=["src", "dst"],
    csv_col_dtypes=["int32", "int32"],
)
hollywood.metadata["is_directed"] = False
europe_osm = Dataset(
    csv_file=RAPIDS_DATASET_ROOT_DIR_PATH / "csv/undirected/europe_osm.csv",
    csv_col_names=["src", "dst"],
    csv_col_dtypes=["int32", "int32"],
)
europe_osm.metadata["is_directed"] = False
cit_patents = Dataset(
    csv_file=RAPIDS_DATASET_ROOT_DIR_PATH / "csv/directed/cit-Patents.csv",
    csv_col_names=["src", "dst"],
    csv_col_dtypes=["int32", "int32"],
)
cit_patents.metadata["is_directed"] = True
soc_livejournal = Dataset(
    csv_file=RAPIDS_DATASET_ROOT_DIR_PATH / "csv/directed/soc-LiveJournal1.csv",
    csv_col_names=["src", "dst"],
    csv_col_dtypes=["int32", "int32"],
)
soc_livejournal.metadata["is_directed"] = True

# Assume all "file_data" (.csv file on disk) datasets are too small to be useful for MG.
undirected_datasets = [
    pytest.param(
        karate,
        marks=[
            pytest.mark.tiny,
            pytest.mark.undirected,
            pytest.mark.file_data,
            pytest.mark.sg,
        ],
    ),
    pytest.param(
        hollywood,
        marks=[
            pytest.mark.small,
            pytest.mark.undirected,
            pytest.mark.file_data,
            pytest.mark.sg,
        ],
    ),
    pytest.param(
        europe_osm,
        marks=[
            pytest.mark.undirected,
            pytest.mark.file_data,
            pytest.mark.sg,
        ],
    ),
]

directed_datasets = [
    pytest.param(
        netscience,
        marks=[
            pytest.mark.small,
            pytest.mark.directed,
            pytest.mark.file_data,
            pytest.mark.sg,
        ],
    ),
    pytest.param(
        email_Eu_core,
        marks=[
            pytest.mark.small,
            pytest.mark.directed,
            pytest.mark.file_data,
            pytest.mark.sg,
        ],
    ),
    pytest.param(
        cit_patents,
        marks=[
            pytest.mark.small,
            pytest.mark.directed,
            pytest.mark.file_data,
            pytest.mark.sg,
        ],
    ),
    pytest.param(
        soc_livejournal,
        marks=[
            pytest.mark.directed,
            pytest.mark.file_data,
            pytest.mark.sg,
        ],
    ),
]

managed_memory = [
    pytest.param(True, marks=[pytest.mark.managedmem_on]),
    pytest.param(False, marks=[pytest.mark.managedmem_off]),
]

pool_allocator = [
    pytest.param(True, marks=[pytest.mark.poolallocator_on]),
    pytest.param(False, marks=[pytest.mark.poolallocator_off]),
]

sg = pytest.param(
    "SG",
    marks=[pytest.mark.sg],
    id="gpu_config=SG",
)
snmg = pytest.param(
    "SNMG",
    marks=[pytest.mark.snmg, pytest.mark.mg],
    id="gpu_config=SNMG",
)
mnmg = pytest.param(
    "MNMG",
    marks=[pytest.mark.mnmg, pytest.mark.mg],
    id="gpu_config=MNMG",
)

karate = pytest.param(
    "karate",
    id="dataset=karate",
)

# RMAT-generated graph options
_rmat_scales = range(16, 31)
_rmat_edgefactors = [4, 8, 16, 32]
rmat = {}
for scale in _rmat_scales:
    for edgefactor in _rmat_edgefactors:
        rmat[f"{scale}_{edgefactor}"] = pytest.param(
            {
                "scale": scale,
                "edgefactor": edgefactor,
            },
            id=f"dataset=rmat_{scale}_{edgefactor}",
        )

# sampling algos length of start list
_batch_sizes = [
    100,
    500,
    1000,
    2500,
    5000,
    10000,
    20000,
    30000,
    40000,
    50000,
    60000,
    70000,
    80000,
    90000,
    100000,
]
batch_sizes = {}
for bs in _batch_sizes:
    batch_sizes[bs] = pytest.param(
        bs,
        id=f"batch_size={bs}",
        marks=[getattr(pytest.mark, f"batch_size_{bs}")],
    )

# sampling algos fanout size
fanout_10_25 = pytest.param(
    [10, 25],
    marks=[pytest.mark.fanout_10_25],
    id="fanout=10_25",
)
fanout_5_10_15 = pytest.param(
    [5, 10, 15],
    marks=[pytest.mark.fanout_5_10_15],
    id="fanout=5_10_15",
)

# scaling the number of concurrent cugraph-service clients
_num_clients = [2, 4, 8, 16, 32]
num_clients = {}
for nc in _num_clients:
    num_clients[nc] = pytest.param(
        nc,
        id=f"num_clients={nc}",
        marks=[getattr(pytest.mark, f"num_clients_{nc}")],
    )

# Parameters for Graph generation fixture
graph_obj_fixture_params = gen_fixture_params(
    (sg, rmat["20_16"]),
    (sg, rmat["24_16"]),
    (snmg, rmat["24_16"]),
    (snmg, rmat["25_16"]),
    (snmg, rmat["26_8"]),
    (snmg, rmat["26_16"]),
    (snmg, rmat["27_16"]),
    (mnmg, rmat["28_16"]),
    (mnmg, rmat["29_16"]),
)
# Uncomment the following test combinations for use with experiments/local dev
"""
graph_obj_fixture_params = gen_fixture_params(
    (sg, karate),
    (sg, rmat["16_4"]),
    (sg, rmat["18_4"]),
    (sg, rmat["20_4"]),
    (sg, rmat["24_4"]),
    (sg, rmat["25_4"]),
    (sg, rmat["26_4"]),
    (snmg, rmat["26_4"]),
    (snmg, rmat["27_4"]),
    (snmg, rmat["28_4"]),
    (mnmg, rmat["29_4"]),
    (mnmg, rmat["30_4"]),
    (snmg, rmat["24_8"]),
    (snmg, rmat["25_8"]),
    (snmg, rmat["27_8"]),
    (snmg, rmat["28_8"]),
    (mnmg, rmat["29_8"]),
    (mnmg, rmat["30_8"]),
    (snmg, rmat["24_16"]),
    (snmg, rmat["25_16"]),
    (snmg, rmat["27_16"]),
    (snmg, rmat["28_16"]),
    (mnmg, rmat["29_16"]),
    (mnmg, rmat["30_16"]),
)
"""
