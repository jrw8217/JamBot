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


minor_scale = [0, 2, 3, 5, 7, 8, 10]
minor_triad_chords = ['m', 'dim', '', 'm', 'm', '', '']
minor_seventh_chords = ['m7', 'm7-5', 'M7', 'm7', 'm7', 'M7', '7']

minor_notes = ['A', 'B', 'C', 'D', 'E', 'F', 'G']



def find_chord_from_root_note(key = 'Am', root_list = [], is_triad = True):
    chord_list = []

    key_number = pm.key_name_to_key_number(key)
    scale_degree = key_number % 12

    if key_number <= 11:     # Major Chord
        for root_note in root_list:
            root_degree = (root_note - scale_degree) % 12



    if key_number > 11 :        # Minor Chord
        for root_note in root_list:
            root_degree = (root_note - scale_degree) % 12
            root_ind = minor_scale.index(root_degree)
            chord_name = minor_notes[root_ind] + minor_triad_chords[root_ind]
            chord_list.append(chord_name)


    return chord_list



def root_note_from_midi(samples_per_bar, fs, name, path, target_path):
    print '---------------------------------------------'
    print name


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
    if len(mid.key_signature_changes) > 0:
        for mid_key in mid.key_signature_changes:
            print 'key:', mid_key.key_number, 'at', mid_key.time
    #else:
        #score = music21.converter.parse(name)
        #key = score.analyze('key')
        #print key.tonic.name, key.mode


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


    #chord_list = find_chord_from_root_note(root_list = root_list)
    #print chord_list





def find_root_note_from_midi_file(tempo_folder, root_note_folder):
    print(tempo_folder)
    for path, subdirs, files in os.walk(tempo_folder):
        for name in files:
            _path = path.replace('\\', '/') + '/'
            _name = name.replace('\\', '/')
            target_path = root_note_folder+_path[len(tempo_folder):]
            if not os.path.exists(target_path):
                os.makedirs(target_path)
            try:
                root_note_from_midi(samples_per_bar, fs, _name, _path, target_path)
            except (ValueError, EOFError, IndexError, OSError, KeyError, ZeroDivisionError) as e:
                exception_str = 'Unexpected error in ' + name  + ':\n', e, sys.exc_info()[0]
                print(exception_str)
#                invalid_files_counter +=1



print('changing Tempo')
change_tempo_folder(source_folder, tempo_folder1)


print('finding root note')
find_root_note_from_midi_file(tempo_folder1, 'data/root')


