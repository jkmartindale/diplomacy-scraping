from bs4 import BeautifulSoup
import lxml # Force an error if lxml isn't importable, since my parsing code is lxml-dependent
import requests
from re import search

class Variant:
    """Represents pre-computed information about a variant"""

    # List of variants registered by `add()``
    registry = []

    def __init__(self, name, supply_centers):
        """Construct a new Variant with a given name and number of supply centers."""
        self.countries = {}
        self.name = name
        self.supply_centers = supply_centers

    @classmethod
    def add(cls, name, supply_centers, excel_table):
        """Process pasted input from Excel to store precomputed variant data under a specified name.
        
        Assumptions this makes:  
        - Fields are separated by tabs  
        - The first non-whitespace line contains column names  
        - Following lines begin with the country name and have the appropriate data following  
        - The first line contains no column for country name  
        - The first line can have leading whitespace, but it doesn't have to  

        These assumptions were made because that's the input William gave me, so blame him.

        This is separate from the constructor because it doesn't make sense that a constructor should depend on a hipster string format.
        """
        # Make and register a lovely new variant
        variant = Variant(name, supply_centers)
        cls.registry.append(variant)

        # Split string into a list of lists
        excel_rows = [line.split('\t') for line in excel_table.split('\n')]

        # Remove leading blank rows
        while excel_rows[0] == ['']:
            excel_rows.pop(0)
        
        # Remove and store header in CSV format
        if excel_rows[0][0] == '':
            excel_rows[0].pop(0) # Remove leading tab
        variant.header = ','.join(excel_rows.pop(0)).strip()

        # Iterate through pre-computed country data
        for row in excel_rows:
            if row == ['']:
                continue
            
            # Remove "Sample " prefix if William still has it in the country name for some reason
            row[0] = row[0][len("Sample "):] if row[0].startswith("Sample ") else row[0]

            # Store pre-computed information as CSV string in a `countries` dict with the country name as the key
            variant.countries[row.pop(0)] = ','.join(row)

###############
# CONFIGURATION
###############

verbose = True

Variant.add("Classic", 34, """
\tZ-score for % starting SCs\tZ-score for distance to edge\tZ-score for % SCs which are neutrals within two moves\tZ-score for other player's starting units within three moves of player's units or SCs
Sample England\t-0.38\t-0.30\t0.53\t-1.38
Sample France\t-0.38\t-0.30\t-1.52\t0.19
Sample Germany\t-0.38\t1.80\t0.53\t1.23
Sample Austria\t-0.38\t0.75\t0.53\t0.45
Sample Russia\t2.27\t-1.35\t0.53\t0.97
Sample Turkey\t-0.38\t-0.30\t0.53\t-1.12
Sample Italy\t-0.38\t-0.30\t-1.52\t-0.34
""")

Variant.add("Modern2", 64, """
\tZ-score for % starting SCs\tZ-score for distance to edge\tZ-score for % SCs which are neutrals within two moves\tZ-score for other player's starting units within three moves of player's units or SCs
Sample Britain\t0.33\t-0.857142857\t0.04\t-1.070882342
Sample France\t0.33\t-0.142857143\t-0.80\t0.642529405
Sample Spain\t-1.33\t0.571428571\t-1.63\t-0.642529405
Sample Germany\t0.33\t1.285714286\t1.30\t0.642529405
Sample Italy\t0.33\t1.285714286\t1.72\t0.214176468
Sample Poland\t-1.33\t1.285714286\t0.04\t1.499235279
Sample Russia\t2.00\t-0.857142857\t-0.38\t1.070882342
Sample Ukraine\t0.33\t-0.142857143\t0.46\t0.214176468
Sample Turkey\t0.33\t-0.857142857\t0.46\t-0.642529405
Sample Egypt\t-1.33\t-1.571428571\t-1.22\t-1.927588216
""")

Variant.add("AncMed", 34, """
\tZ-score for % starting SCs\tZ-score for distance to edge\tZ-score for % SCs which are neutrals within two moves\tZ-score for other player's starting units within three moves of player's units or SCs
Sample Carthage\t0.00\t0\t-1.07\t0.5
Sample Rome\t0.00\t1.118033989\t0.27\t0.5
Sample Greece\t0.00\t1.118033989\t1.60\t0.5
Sample Egypt\t0.00\t-1.118033989\t-1.07\t0.5
Sample Persia\t0.00\t-1.118033989\t0.27\t-2
""")

Variant.add("WWII", 74, """
\tZ-score for % starting SCs\tZ-score for distance to edge\tZ-score for % SCs which are neutrals within two moves\tZ-score for other player's starting units within three moves of player's units or SCs
Sample Britain\t0.00\t0\t-0.177393719\t-0.8125
Sample France\t0.00\t0\t-1.655674709\t1.0625
Sample Germany\t0.00\t1.58113883\t1.300887271\t1.0625
Sample Italy\t0.00\t0\t0.709574875\t0.125
Sample Soviet Russia\t0.00\t-1.58113883\t-0.177393719\t-1.4375
""")

Variant.add("TreatyOfVerdun", 15, """
\tZ-score for % starting SCs\tZ-score for distance to edge\tZ-score for % SCs which are neutrals within two moves\tZ-score for other player's starting units within three moves of player's units or SCs
West Francia\t0\t0\t0\t0.707106781
Middle Francia\t0\t0\t0\t-1.414213562
East Francia\t0\t0\t0\t0.707106781
""")

Variant.add("SouthAmerica4", 24, """
\tZ-score for % starting SCs\tZ-score for distance to edge\tZ-score for % SCs which are neutrals within two moves\tZ-score for other player's starting units within three moves of player's units or SCs
Colombia\t-0.577350269\t-0.577350269\t-1.53\t-1.677484274
Brazil\t1.732050808\t-0.577350269\t0.12\t0.762492852
Chile\t-0.577350269\t-0.577350269\t0.12\t0.15249857
Argentina\t-0.577350269\t1.732050808\t1.28\t0.762492852
""")

#######################
# ACTUAL SCRIPT I GUESS
#######################

for variant in Variant.registry:
    with open('%0s.csv' % variant.name, 'w+') as csv:

        # Find variant ID
        response = requests.get('https://vdiplomacy.com/gamelistings.php?page-games=1&gamelistType=Finished&searchOn=on')
        soup = BeautifulSoup(response.text, 'lxml')
        variantID = soup(text=variant.name)[0].parent['value']
        
        # Build CSV header
        csv.write('Game ID,Country,' + variant.header + ',Number of players,% Supply Centers at game end\n')

        page = 1
        while True: # I can't figure out an easy loop condition, since vDiplomacy returns 200 on out-of-bounds search pages
            # Download page
            response = requests.post('https://vdiplomacy.com/gamelistings.php?gamelistType=Finished&page-games=%d' % page, data=[
                # Tuples are used because vDiplomacy uses duplicate keys for messaging rules, so a dict won't work
                ('search[chooseVariant]', variantID),
                ('search[pressType][]', 'PublicPressOnly'),
                ('search[pressType][]', 'Regular'),
                ('search[pressType][]', 'RulebookPress'),
                # Exclude gunboat games for the purposes of this study
            ])
            if search('The set of returned games has finished', response.text):
                break
            soup = BeautifulSoup(response.text, 'lxml')
            
            # `gamePanel` divs contain game information
            for game in soup(class_='gamePanel'):
                game_ID = search('(?<=gameID=)\d+', str(game))[0]
                if verbose: print('Variant: %s, Page: %d, Game ID: %s' % (variant.name, page, game_ID))

                # Grab members from only the first table under the `membersList` div, since the second table, "Civil Disorders", contains duplicate information
                countries = game.find(class_="membersList").table(class_="member")
                players = str(len(countries))
                for country in countries:
                    precomputed_values = variant.countries[country.find(class_="memberCountryName").text.strip()]
                    
                    supply_centers_match = search('\d+(?= supply-centers)', country.find(class_="memberGameDetail").text)
                    percent_SCs = str(int(supply_centers_match[0]) / variant.supply_centers) if supply_centers_match else '0'

                    csv.write(','.join([game_ID, precomputed_values, players, percent_SCs]) + '\n')
            
            page += 1