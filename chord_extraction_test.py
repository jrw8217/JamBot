from settings import *
import numpy as np
import midi_functions as mf
import pickle
import os
import sys
import pretty_midi as pm
import mido
from collections import Counter
from data_processing import change_tempo_folder
import music21


'''
Chord matching

Major 
C : CM7, Dm7, Em7, FM7, G7, Am7, Bm7-5      (seventh chord)
C : C, Dm, Em, F, G, Am, Bdim               (triad chord)


Minor
C : Cm7, Dm7-5, EbM7, Fm7, Gm7, AbM7, Bb7       (seventh chord)
C : Cm, Ddim, Eb, Fm, Gm, Ab, Bb                (triad chord)




'''


major_scale = [0, 2, 4, 5, 7, 9, 11]
major_triad_chords = ['', 'm', 'm', '', '', 'm', 'dim']
major_seventh_chords = ['M7', 'm7', 'm7', 'M7', '7', 'm7', 'm7-5']

major_notes = [['C', 'D', 'E', 'F', 'G', 'A', 'B'], ['Db', 'Eb', 'F', 'Gb', 'Ab', 'Bb', 'C'], ['D', 'E', 'F#', 'G', 'A', 'B', 'C#'],
               ['Eb', 'F', 'G', 'Ab', 'Bb', 'C', 'D'], ['E', 'F#', 'G#', 'A', 'B', 'C#', 'D#'], ['F', 'G', 'A', 'Bb', 'C', 'D', 'E'],
               ['F#', 'G#', 'A#', 'B', 'C#', 'D#', 'E#'], ['G', 'A', 'B', 'C', 'D', 'E', 'F#'], ['Ab', 'Bb', 'C', 'Db', 'Eb', 'F', 'G'],
               ['A' ,'B', 'C#', 'D', 'E', 'F#', 'G#'], ['Bb', 'C', 'D', 'Eb', 'F', 'G', 'A'], ['B', 'C#', 'D#', 'E', 'F#', 'G#', 'A#']]


minor_scale = [0, 2, 3, 5, 7, 8, 10]
minor_triad_chords = ['m', 'dim', '', 'm', 'm', '', '']
minor_seventh_chords = ['m7', 'm7-5', 'M7', 'm7', 'm7', 'M7', '7']

minor_notes = [['C', 'D', 'Eb', 'F', 'G', 'Ab', 'Bb'], ['C#', 'D#', 'E', 'F#', 'G#', 'A', 'B'], ['B', 'C#', 'D', 'E', 'F#', 'G', 'A'],
               ['Eb', 'F', 'Gb', 'Ab', 'Bb', 'Cb', 'Db'], ['E', 'F#', 'G', 'A', 'B', 'C', 'D'], ['F', 'G', 'Ab', 'Bb', 'C', 'Db', 'Eb'],
               ['F#', 'G#', 'A', 'B', 'C#', 'D', 'E'], ['G', 'A', 'Bb', 'C', 'D', 'Eb', 'F'], ['Ab', 'Bb', 'Cb', 'Db', 'Eb', 'Fb', 'Gb'],
               ['A', 'B', 'C', 'D', 'E', 'F', 'G'], ['Bb', 'C', 'Db', 'Eb', 'F', 'Gb', 'Ab'], ['B', 'C#', 'D', 'E', 'F#', 'G', 'A']
               ]



def find_chord_from_root_note(key = 0, root_list = [], is_triad = True):
    chord_list = []

    #key_number = pm.key_name_to_key_number(key)
    scale_degree = key % 12

    if key <= 11:     # Major Chord
        for root_note in root_list:
            root_degree = (root_note - scale_degree) % 12

            if root_degree in major_scale:
                root_ind = major_scale.index(root_degree)
                chord_name = major_notes[scale_degree][root_ind] + major_seventh_chords[root_ind]
                chord_list.append(chord_name)

            else:
                chord_list.append('-')


    if key > 11 :        # Minor Chord
        for root_note in root_list:
            root_degree = (root_note - scale_degree) % 12

            if root_degree in minor_scale:
                root_ind = minor_scale.index(root_degree)
                chord_name = minor_notes[scale_degree][root_ind] + minor_seventh_chords[root_ind]
                chord_list.append(chord_name)

            else:
                chord_list.append('-')

    return chord_list



def root_note_from_midi(samples_per_bar, fs, name, path, target_path):
    print '---------------------------------------------'
    print path + '/' + name


    #piano_roll = mf.get_pianoroll(name, path, fs)

    # Get piano roll
    mid = pm.PrettyMIDI(path + name)
    if double_sample_notes:
        piano_roll = mf.double_sample(mid)
    else:
        piano_roll = mid.get_piano_roll(fs=fs)

    for i, _ in enumerate(piano_roll):
        for j, _ in enumerate(piano_roll[i]):
            if piano_roll[i, j] != 0:
                piano_roll[i, j] = 1


    # Get Key
    key = 0
    if len(mid.key_signature_changes) > 0:
        key = mid.key_signature_changes[0].key_number   # ignore key change

    else:
        print name, 'does not have any key_signature_change'
        return -1

    print 'key: ', key


    # Get the root note of each bar
    root_list = []
    for i in range(0, piano_roll.shape[1] - samples_per_bar + 1, samples_per_bar):
        bar = np.sum(piano_roll[:, i : i + samples_per_bar], axis=1)
        #print bar

        root_note = 0
        for note in range(len(bar)):
            if bar[note] != 0:
                root_note = note
                break

        #print root_note, bar[root_note]
        root_list.append(root_note)


    chord_list = find_chord_from_root_note(key = key, root_list = root_list)
    print chord_list
    pickle.dump(chord_list, open(target_path + name + '_chord.pickle', 'wb'))





def find_root_note_from_midi_file(tempo_folder, root_note_folder):
    print(tempo_folder)
    for path, subdirs, files in os.walk(tempo_folder):
        print(subdirs)
        for name in files:
            _path = path.replace('\\', '/') + '/'
            _name = name.replace('\\', '/')
            target_path = root_note_folder+_path[len(tempo_folder):]
            if not os.path.exists(target_path):
                os.makedirs(target_path)
            try:
                root_note_from_midi(samples_per_bar, fs, _name, _path, target_path)
            except (ValueError, EOFError, IndexError, OSError, KeyError, ZeroDivisionError, IOError) as e:
                exception_str = 'Unexpected error in ' + name  + ':\n', e, sys.exc_info()[0]
                print(exception_str)
#                invalid_files_counter +=1



print('changing Tempo')
change_tempo_folder('Beatles', 'Beatles_tempo')


print('finding chord')
find_root_note_from_midi_file('Beatles_tempo', 'Beatles_chord')


