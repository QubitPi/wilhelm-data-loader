# Copyright Jiaqi Liu
#
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
from datasets import load_dataset

from wilhelm_python_sdk.database_clients import get_database_client


def load_into_database():
    dataset = load_dataset("QubitPi/wilhelm-vocabulary")

    with get_database_client() as database_client:
        graph = dataset["German"].iter(batch_size=1)
        for triple in graph:
            database_client.save_a_node_with_attributes("Term", triple["source"])


if __name__ == "__main__":
    load_into_database()