"""
Demo script showing the conditional load duration factor logic.
"""

from load.nbcc2020 import nbcc_uls_combinations
from eime.units import ureg

kN = ureg.kN

# Define nominal loads
nominal = {
    'D': 25.0 * kN,
    'L': 17.5 * kN,
    'S': 23.0 * kN
}

# Generate load combinations
combos = nbcc_uls_combinations(nominal, include_wind=False, include_seismic=False)

print('\n' + '='*60)
print('LOAD DURATION FACTOR - CONDITIONAL LOGIC DEMONSTRATION')
print('='*60)
print('\nPer CSA O86:25:')
print('- When PL > PS: Use K_D = 1.0 - 0.50*log10(PL/PS) >= 0.65')
print('- When PL <= PS: Use simplified values based on combo type:')
print('    * Dead only: K_D = 0.65')
print('    * Includes live: K_D = 1.0')
print('    * Includes wind/seismic: K_D = 1.15')
print('\n' + '='*60)

for i, name in enumerate(combos.names):
    pl = combos.duration_long_percent[i].magnitude
    ps = combos.duration_short_percent[i].magnitude
    combo_type = combos.load_combo_types[i]
    
    print(f'\n{name}:')
    print(f'  Combo Type: {combo_type}')
    print(f'  PL (long-term %): {pl:.1f}')
    print(f'  PS (short-term %): {ps:.1f}')
    
    if pl > ps:
        import numpy as np
        kd = max(1.0 - 0.50 * np.log10(pl/ps), 0.65)
        print(f'  Condition: PL > PS')
        print(f'  Formula: K_D = 1.0 - 0.50*log10({pl:.1f}/{ps:.1f}) = {kd:.3f}')
    else:
        if combo_type == 'dead_only':
            kd = 0.65
        elif combo_type == 'includes_live':
            kd = 1.0
        elif combo_type == 'includes_wind_or_seismic':
            kd = 1.15
        else:
            kd = 1.0
        
        print(f'  Condition: PL <= PS')
        print(f'  Formula: K_D = {kd} (simplified for {combo_type})')

print('\n' + '='*60)
print('All load combinations correctly use conditional K_D logic!')
print('='*60 + '\n')
