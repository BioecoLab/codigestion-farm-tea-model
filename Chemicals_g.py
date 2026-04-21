
'Chemicals'

import biosteam as bst
import thermosteam as tmo


def create_chemicals(VS_density, Ash_density):
    chemicals = bst.Chemicals([
        bst.Chemical('VolatileSolids',  # Volatile Solids
                     rho=VS_density,
                     Cp=1.100,
                     search_db=False,
                     phase='s',
                     MW=1,
                     default=True),
        bst.Chemical('Ash',  # Non-Volatile Solids
                     rho = Ash_density,
                     Cp=1.100,
                     search_db=False,
                     phase='s',
                     MW=1,
                    default=True),
        bst.Chemical('CH4',
                     search_db=True,
                     phase='g'),
        bst.Chemical('CO2',
                     search_db=True,
                     phase='g'),
        bst.Chemical('O2',
                     search_db=True),
        bst.Chemical('Water',
                     search_db=True)
    ])
    return chemicals
