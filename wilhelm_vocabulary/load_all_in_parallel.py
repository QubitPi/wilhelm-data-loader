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

from multiprocessing import Process
from multiprocessing import Queue

import load_ancient_greek
import load_german
import load_latin

if __name__ == "__main__":
    queue = Queue()

    latin = Process(target=load_latin.load_into_database(), args=(queue, ))
    german = Process(target=load_german.load_into_database(), args=(queue, ))
    ancient_greek = Process(target=load_ancient_greek.load_into_database(), args=(queue, ))

    latin.start()
    german.start()
    ancient_greek.start()

    # Blocking
    result = queue.get()