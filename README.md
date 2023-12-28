# ask-iea

[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

Retrieval-Augmented Generation (RAG) chatbot to retrieve information from the [IEA (International Energy Agency)](https://www.iea.org/) reports with citation. Build with [LangChain](https://www.langchain.com/) and [FAISS](https://github.com/facebookresearch/faiss).

This is a prototype to play around and test the potential of an RAG approach. All publicly available IEA reports can be queried (own OpenAI API key required). A two-step system is used to identify and retrieve relevant sources, similar to [paperqa](https://github.com/whitead/paper-qa). The results are already quite promising, but there is a lot of room to try out different splitters, retrievers and prompts. GPT-4 leads to better results, but GPT-3 is used.


## Installation
Just clone the repository and install the requirements.

```bash
git clone https://github.com/lkstrp/ask-iea.git
cd ask-iea
pip install -r requirements.txt
```

## Example

When running the first time, the latest IEA reports are scraped and added to the vectorstore. This can take a while, depending on the number of reports. All reports could be added, but the retrieval quality decreases. The vectorstore is saved in the user directory under `.ask-iea`.

```python
import ask_iea
ask_iea.update(first_n=50)
answer = ask_iea.ask('How is the energy transition influencing the operation of electricity grids?')
print(answer)
```

### Output

>**Answer:**
>
>The energy transition is influencing the operation of electricity grids in several ways. It necessitates the creation of remuneration structures that reward investments in efficient, modern grids. The integration of renewable energy, implementation of digital and smart grid technologies, grid modernization, enhanced grid resilience and security, electrification of transport, decentralization of generation, increase in distributed energy resources, and integration of energy storage are all part of this transition. Additionally, the electrification trend in the buildings sector is increasing the need for grid management, visibility, and controllability. Significant development of distribution grids is needed to integrate renewables, including the deployment of digitalisation to manage the increasing complexity of systems due to distributed resources.
>
>**Sources:**
>
>Electricity grids, which have been crucial to power systems for over a century, are becoming increasingly important as clean energy transitions progress. The pace of electrification and deployment of renewables is increasing, but without sufficient grids to connect new electricity supply with demand, clean energy transitions could stall. Current indications suggest that grids are becoming a bottleneck to clean energy transitions. If grid development and reform do not progress quickly enough, there could be prolonged reliance on fossil fuels, leading to increased emissions and societal costs.\
>*Page 2 | Electricity Grids and Secure Energy Transitions*\
>[Link](https://iea.blob.core.windows.net/assets/ea2ff609-8180-4312-8de9-494bcf21696d/ElectricityGridsandSecureEnergyTransitions.pdf#page=17https://iea.blob.core.windows.net/assets/ea2ff609-8180-4312-8de9-494bcf21696d/ElectricityGridsandSecureEnergyTransitions.pdf#page=2)
>
>The energy transition is influencing the operation of electricity grids by necessitating the creation of remuneration structures that reward investments in efficient, modern grids. New technologies and practices, such as increased battery storage and microgrids, are emerging as alternatives to traditional infrastructure. However, new poles and wires are still needed. Policymakers are required to create frameworks for grid transformation, modernization, and expansion. This involves balancing cost, acceptability, and sustainability, and requires innovation and investment from the private sector.\
>*Page 12 | Electricity Grids and Secure Energy Transitions*\
>[Link](https://iea.blob.core.windows.net/assets/ea2ff609-8180-4312-8de9-494bcf21696d/ElectricityGridsandSecureEnergyTransitions.pdf#page=17https://iea.blob.core.windows.net/assets/ea2ff609-8180-4312-8de9-494bcf21696d/ElectricityGridsandSecureEnergyTransitions.pdf#page=12)
>
>The transition to renewable energy is causing a bottleneck in electricity grids, with 3,000 gigawatts of renewable power projects, including 1,500 gigawatts in advanced stages, waiting in grid connection queues. This is five times the amount of solar PV and wind capacity added in 2022. Despite a rapid increase in investment in renewables, global investment in grids has remained static at around USD 300 billion per year. Delays in grid investment and reform could increase global carbon dioxide emissions and slow energy transitions.\
>*Page 9 | Electricity Grids and Secure Energy Transitions*\
>[Link](https://iea.blob.core.windows.net/assets/ea2ff609-8180-4312-8de9-494bcf21696d/ElectricityGridsandSecureEnergyTransitions.pdf#page=17https://iea.blob.core.windows.net/assets/ea2ff609-8180-4312-8de9-494bcf21696d/ElectricityGridsandSecureEnergyTransitions.pdf#page=9)
>
>The energy transition is influencing the operation of electricity grids through the integration of renewable energy, implementation of digital and smart grid technologies, grid modernization, enhanced grid resilience and security, electrification of transport, decentralization of generation, increase in distributed energy resources, and integration of energy storage. Grid expansion, particularly at the distribution level in EMDEs, has grown by over 40% in the past decade due to these changes.\
>*Page 17 | Electricity Grids and Secure Energy Transitions*\
>[Link](https://iea.blob.core.windows.net/assets/ea2ff609-8180-4312-8de9-494bcf21696d/ElectricityGridsandSecureEnergyTransitions.pdf#page=17)
>
>The energy transition is influencing the operation of electricity grids by increasing the need for grid management, visibility, and controllability. The electrification trend in the buildings sector, driven by heat pump installations, is increasing each year. To integrate renewables, significant development of distribution grids is needed, including the deployment of digitalisation to manage the increasing complexity of systems due to distributed resources. This includes investment in smart meters, remote control, and communication and automation across the low- and medium-voltage grids.\
>*Page 80 | Electricity Grids and Secure Energy Transitions*\
>[Link](https://iea.blob.core.windows.net/assets/ea2ff609-8180-4312-8de9-494bcf21696d/ElectricityGridsandSecureEnergyTransitions.pdf#page=80)
>
>
>Checked the following reports:
>- The Role of E-fuels in Decarbonising Transport
>- Overcoming the Energy Trilemma: Secure and Inclusive Transitions
>- The Evolution of Energy Efficiency Policy to Support Clean Energy Transitions
>- Leveraging Fossil Fuel Capabilities for Clean Energy Transitions
>- CCUS Policies and Business Models: Building a Commercial Market
>- Institutional Architecture for Regional Power System Integration
>- Electricity Grids and Secure Energy Transitions
>- The Imperative of Cutting Methane from Fossil Fuels
>- Efficient Grid-Interactive Buildings
>- Net Zero Roadmap: A Global Pathway to Keep the 1.5 °C Goal in Reach
