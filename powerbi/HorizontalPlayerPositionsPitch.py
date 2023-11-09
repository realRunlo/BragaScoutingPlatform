from mplsoccer import Pitch
import matplotlib.pyplot as plt

def write_text_on_labels_from_powerbi(positions, dataset, ax):
    dataset['code'] = dataset['code'].str.upper()

    for i, position in enumerate(positions, 1):
        x = position[0] * FIGWIDTH
        y = position[1] * FIGHEIGHT
        label = position[2]
        
        if label in dataset['code'].values:
            percent_value = dataset[dataset['code'] == label]['percent'].values[0]
            ax.scatter(x, y, color='red', s=1000, zorder=2)
            ax.text(x, y+7, f'{percent_value}%', color='white', ha='center', va='center', fontsize=12, weight='bold')
        else:
            ax.scatter(x, y, color='red', s=1000, zorder=2)
        
        #ax.text(x, y, str(i), color='white', ha='center', va='center', fontsize=12)
        ax.text(x, y, label, color='white', ha='center', va='center', fontsize=12)

FIGWIDTH = 7
FIGHEIGHT = 8
NROWS = 1
NCOLS = 1
SPACE = 0
MAX_GRID = 1

PAD_TOP = 2
PAD_BOTTOM = 2
PAD_SIDES = ((100 + PAD_TOP + PAD_BOTTOM) * FIGWIDTH / FIGHEIGHT - 80) / 2
pitch = Pitch(pitch_type="wyscout",
              pad_top=PAD_TOP, pad_bottom=PAD_BOTTOM,
              pad_left=PAD_SIDES, pad_right=PAD_SIDES,
              pitch_color='grass', stripe=True, line_color='white')

GRID_WIDTH, GRID_HEIGHT = pitch.grid_dimensions(figwidth=FIGWIDTH, figheight=FIGHEIGHT,
                                                nrows=NROWS, ncols=NCOLS,
                                                max_grid=MAX_GRID, space=SPACE)
TITLE_HEIGHT = 0
ENDNOTE_HEIGHT = 0

fig, ax = pitch.grid(figheight=FIGHEIGHT, grid_width=GRID_WIDTH,
                     grid_height=GRID_HEIGHT, space=SPACE,
                     ncols=NCOLS, nrows=NROWS, title_height=TITLE_HEIGHT,
                     endnote_height=ENDNOTE_HEIGHT, axis=True)

UPLINE = 2 
MIDLINE = 6
LOWERLINE = 10

team_positions = [
                    (4, LOWERLINE, "LB"),                                          (13, LOWERLINE, 'LW'),
(1, MIDLINE, 'GK'), (4, MIDLINE, 'CB'), (7, MIDLINE, 'DMF'), (10, MIDLINE, 'CMF'), (13, MIDLINE, 'AMF'), (16, MIDLINE, 'CF'),
                    (4, UPLINE, "RB"),                                             (13, UPLINE, 'RW'),
]

import pandas as pd

#Dados de teste

data = {'code': ['GK', 'RB'],
        'percent': [40, 50]}
dataset = pd.DataFrame(data)

write_text_on_labels_from_powerbi(team_positions, dataset, ax)

plt.show()
