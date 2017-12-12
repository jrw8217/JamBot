import pretty_midi as pm
import numpy as np
import os
import sys
import pickle




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




def find_chord_from_bass_note(key = 0, note_list = []):
    chord_list = []

    #key_number = pm.key_name_to_key_number(key)
    scale_degree = key % 12

    if key <= 11:     # Major Chord
        for root_note in note_list:
            root_degree = (root_note - scale_degree) % 12

            if root_degree in major_scale:
                root_ind = major_scale.index(root_degree)
                chord_name = major_notes[scale_degree][root_ind] + major_seventh_chords[root_ind]
                chord_list.append(chord_name)

            else:
                chord_list.append('-')


    if key > 11 :        # Minor Chord
        for root_note in note_list:
            root_degree = (root_note - scale_degree) % 12

            if root_degree in minor_scale:
                root_ind = minor_scale.index(root_degree)
                chord_name = minor_notes[scale_degree][root_ind] + minor_seventh_chords[root_ind]
                chord_list.append(chord_name)

            else:
                chord_list.append('-')

    return chord_list


    #print 'tempo: ', mid.get_tempo_changes()[1]



def get_key_and_bass_note_from_midi(name, path):
    print '-----------------------------------------------------------'
    print name

    mid = pm.PrettyMIDI(path + name)
    print 'Instruments: ', mid.instruments

    # Get key
    if len(mid.key_signature_changes) > 0:
        key = mid.key_signature_changes[0].key_number  # ignore key changes

    else:
        print name, 'does not have any key_signature_change'
        return -1

    #Get bass note
    bass_counter = 0
    #bass_piano_roll = []

    for instrument in mid.instruments:
        if bass_counter > 0:   # check the first bass only
            break

        if instrument.program < 40 and instrument.program > 31: # find bass from program number
            print instrument.name
            bass_piano_roll = np.copy(instrument.get_piano_roll(fs=2))
            bass_counter += 1

    if bass_counter == 0:
        print name, 'does not have any bass instrument'
        return -1

    bass_note = []

    print bass_piano_roll.shape[1]
    for half_note in range(bass_piano_roll.shape[1]):

        notes = bass_piano_roll[:, half_note].nonzero()[0]

        if notes.size != 0:
            note = notes[0]

        else:
            note = -1

        bass_note.append(note)


    print key, bass_note
    return key, bass_note



def find_chord_from_midi_file(midi_folder, target_folder):
    invalid_files_counter = 0

    for path, subdirs, files in os.walk(midi_folder):
        for name in files:
            _path = path.replace('\\', '/') + '/'
            _name = name.replace('\\', '/')
            target_path = target_folder+_path[len(midi_folder):]

            if not os.path.exists(target_path):
                os.makedirs(target_path)

            try:
                # Get key and bass note
                key, bass_note = get_key_and_bass_note_from_midi(_name, _path)

                # Get chord
                chord_list = find_chord_from_bass_note(key=key, note_list=bass_note)
                print chord_list

                pickle.dump(chord_list, open(target_path + _name + '_chord.pickle', 'wb'))

            except:
                exception_str = 'Unexpected error in ' + name,  sys.exc_info()[0]
                print(exception_str)
                invalid_files_counter += 1

    #print key_counter
    #print invalid_files_counter

    #pickle.dump(key_counter, open(midi_folder + '/key_counter_of_' + midi_folder + '.pickle', 'wb'))




find_chord_from_midi_file('Yesterday_with_bass', 'Yeaterday_with_bass_chord')