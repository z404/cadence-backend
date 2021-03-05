"""
Standalone program to test the usage of snips-nlu package
Snips-nlu is a NLP package, that helps get a basic understanding of given text
Features:
 - Intent Extraction
   - Snips NLU requires that it be trained with a yaml file, containing sample inputs and their intents
   - Once the engine is trained with this dataset, it can quite accurately predict the intent of the name
   - This intent is later returned to the program by the engine.parse() function
 - Slot Extraction
   - Some strings have more information in them than just intents. (For example: Wake me up at 10am. Intent = #WakeUp. Slot: 10 am)
   - Snips NLU can extract slots from strings fairly easily. Custom slots can also be created.
   - These slots, if any, are returned by the same function along with the intents
   - Synonyms can be declared, like evening/dusk, so slots can be managed by the program easily
 - Builtin Entities
   - Strings like "tommorow at 10:00" will be automatically evaluated by Snips NLU to give a datetime object for 10:00 the next day
Advantages:
 - Easy to use
 - Not much work in training dataset if there are few intents
 - Slots are very easy to extract
 - Entire module works offline. No cloud interaction required, unlike RasaNLU etc.
 - Well documented
Snips NLU requires a lot of pre-requisites when installing the package. It needs to have setuptools-rust installed, as well as the RUST compiler added to PATH.
After Snips NLU is installed, the English language needs to be downloaded. This can be done with the command: "python -m snips-nlu download en"
This command creates a symbolic link, but doesnt have permissions to do so on windows, so this command needs to be run in an elevated command prompt
"""
import os

from snips_nlu import SnipsNLUEngine
from snips_nlu.dataset import dataset
from snips_nlu.default_configs import CONFIG_EN

# Training the Engine
engine = SnipsNLUEngine(config=CONFIG_EN)
# Creating the dataset
data = dataset.Dataset.from_yaml_files(
    "en", ["./trainyaml/" + i for i in os.listdir("./trainyaml/") if ".yaml" in i]
)
# Training the engine (one time train, can be pickled
# This train takes about 4 seconds with the current dataset. The main program may take up to 15 seconds
engine.fit(data)

inp = input("Enter a string to find its intent: ")
# Parsing the input (output is instant, no delay here)
parsing = engine.parse(inp)
# Printing the dictionary object of information received
print(parsing)
