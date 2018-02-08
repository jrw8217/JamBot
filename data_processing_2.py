from settings import *
import numpy as np
import midi_functions as mf
import pickle
import os
import sys
import pretty_midi as pm
import mido
from collections import Counter
import json
from scipy.sparse import csc_matrix
from midi_functions import *


def msd_id_to_dirs(msd_id):
    return os.path.join(msd_id[2], msd_id[3], msd_id[4], msd_id)


def load_npz(file_):
    """Load a npz file that contains numpy arrays or scipy csc matrices.
    Parameters
    ----------
    file_ : str or file-like object
        String that indicates the path to save the file or an opened file where
        the data will be loaded.
    Returns
    -------
    result : dict of np.array or scipy.sparse.csc_matrix
        A dictionary that contains the loaded data. The keys are the file names
        in the npz file and the values are the data. If all files are identified
        as sparse matrices (by its filename), the data will be converted back to
        scipy csc matrices.
    """
    with np.load(file_) as loaded:
        non_sparse_keys = [key for key in loaded.files if "_csc_" not in key]
        if non_sparse_keys:
            result = {key: loaded[key] for key in loaded.files}
        else:
            # if non_sparse matrices found, group arrays coming from the same
            # csc_matrix and convert them back to one csc_matrix
            keys = sorted(loaded.files)
            result = {}
            for idx in range(int(len(keys)/4)):
                key = keys[4*idx][:-9] # remove '_csc_data' to get matrix name
                result[key] = csc_matrix((loaded[keys[4*idx]],
                                          loaded[keys[4*idx+1]],
                                          loaded[keys[4*idx+2]]),
                                         shape=loaded[keys[4*idx+3]])
    return result


def get_dirs(base_dir):
    dirs = []

    json_path = os.path.join(base_dir, 'midis.json')
    with open(json_path, 'r') as f:
        midis = json.load(f)

    song_list = midis.keys()
    for song in song_list:
        midi_list = midis[song].keys()
        for midi in midi_list:
            _dir = os.path.join(base_dir, msd_id_to_dirs(song), midi)
            dirs.append(_dir)

    return dirs


def testttt(path):
    chord_cntr = Counter()

    # make chord for each path
    paths = get_dirs(path)
    chord_dict = {}
    for _path in paths:
        filepath = os.path.join(_path, 'piano_rolls.npz')

        pianorolls = load_npz(filepath)

        idx = 0
        for track_num, track in pianorolls.items():
            track_arr = track.toarray()
            if idx == 0:
                total = np.zeros_like(track_arr)

            total += track_arr

        total[total > 0] = 1

        histo_bar = pianoroll_to_histo_bar(total, samples_per_bar)
        histo_oct = histo_bar_to_histo_oct(histo_bar, octave)
        chords = histo_to_chords(histo_oct, chord_n)

        for chord in chords:
            if chord in chord_cntr:
                chord_cntr[chord] += 1
            else:
                chord_cntr[chord] = 1

        chord_dict[_path] = chords

    # make chord dict
    cntr = chord_cntr.most_common(n=num_chords - 1)

    chord_to_index = dict()
    chord_to_index[UNK] = 0
    for chord, _ in cntr:
        chord_to_index[chord] = len(chord_to_index)
    index_to_chord = {v: k for k, v in chord_to_index.items()}
    pickle.dump(chord_to_index, open(path + '/chord_to_index.pkl', 'wb'))
    pickle.dump(index_to_chord, open(path + '/index_to_chord.pkl', 'wb'))

    # make jambot style chord for each midi
    for _path in paths:
        chords = chord_dict[_path]

        chords_index = []
        for chord in chords:
            if chord in chord_to_index:
                chords_index.append(chord_to_index[chord])
            else:
                chords_index.append(chord_to_index[UNK])

        with open(_path+'/jambot_chord.pkl', 'wb') as f:
            pickle.dump(chords_index, f)


def get_scales():
    # get all scales for every root note
    dia = tuple((0,2,4,5,7,9,11))
    diatonic_scales = []
    for i in range(0,12):
        diatonic_scales.append(tuple(np.sort((np.array(dia)+i)%12)))
    
    harm = tuple((0,2,4,5,8,9,11))
    harmonic_scales = []
    for i in range(0,12):
        harmonic_scales.append(tuple(np.sort((np.array(harm)+i)%12)))
    
    mel = tuple((0,2,4,6,8,9,11))
    melodic_scales = []
    for i in range(0,12):
        melodic_scales.append(tuple(np.sort((np.array(mel)+i)%12)))
    blue = tuple((0,3,5,6,7,10))
    blues_scales = []
    for i in range(0,12):
        blues_scales.append(tuple(np.sort((np.array(blue)+i)%12)))
    
    
    return diatonic_scales, harmonic_scales, melodic_scales, blues_scales


def get_shift(scale):
    diatonic_scales, harmonic_scales, melodic_scales, blues_scales = get_scales()
    if scale in diatonic_scales:
        return diatonic_scales.index(scale)
#    elif scale in harmonic_scales:
#        return harmonic_scales.index(scale)
#    elif scale in melodic_scales:
#        return melodic_scales.index(scale)
    else:
        return 'other'



def shift_midi_files(song_histo_folder,tempo_folder,shifted_folder):
    for path, subdirs, files in os.walk(song_histo_folder):
        for name in files:
            _path = path.replace('\\', '/') + '/'
            _name = name.replace('\\', '/')
            tempo_path = tempo_folder+_path[len(song_histo_folder):]
            target_path = shifted_folder+_path[len(song_histo_folder):]
            song_histo = pickle.load(open(_path + _name, 'rb'))
            key = mf.histo_to_key(song_histo, key_n)
            shift = get_shift(key)
            _name = _name[:-7]
            if shift != 'other':
                if not os.path.exists(target_path):
                    os.makedirs(target_path)
                try:
                    mf.shift_midi(shift, _name, tempo_path, target_path)
                except (ValueError, EOFError, IndexError, OSError, KeyError, ZeroDivisionError) as e:
                    exception_str = 'Unexpected error in ' + name  + ':\n', e, sys.exc_info()[0]
                    print(exception_str)


def count_scales():
    # get all scales for every root note
    diatonic_scales, harmonic_scales, melodic_scales, blues_scales = get_scales()

    scale_cntr = Counter()
    other_cntr = Counter()
    for path, subdirs, files in os.walk(song_histo_folder):
        for name in files:
            _path = path.replace('\\', '/') + '/'
            _name = name.replace('\\', '/')
            song_histo = pickle.load(open(_path + _name, 'rb'))
            key = mf.histo_to_key(song_histo, key_n)
            if key in diatonic_scales:
                scale_cntr['diatonic'] +=1
                          
            elif key in harmonic_scales:
                scale_cntr['harmonic'] +=1
                          
            elif key in melodic_scales:
                scale_cntr['melodic'] +=1
            elif key[:-1] in blues_scales:
                scale_cntr['blues'] +=1
            else:
                scale_cntr['other'] += 1
                other_cntr[key] +=1
    return scale_cntr, other_cntr
    

def count_keys():
    key_cntr = Counter()
    for path, subdirs, files in os.walk(song_histo_folder):
        for name in files:
            _path = path.replace('\\', '/') + '/'
            _name = name.replace('\\', '/')
            song_histo = pickle.load(open(_path + _name, 'rb'))
            key = mf.histo_to_key(song_histo, key_n)
            if key in key_cntr:
                key_cntr[key] +=1
            else:
                key_cntr[key] = 1                    
    return key_cntr


def save_song_histo_from_histo(histo_folder,song_histo_folder):
    for path, subdirs, files in os.walk(histo_folder):
        for name in files:
            _path = path.replace('\\', '/') + '/'
            _name = name.replace('\\', '/')
            target_path = song_histo_folder+_path[len(histo_folder):]
            if not os.path.exists(target_path):
                os.makedirs(target_path) 
            mf.load_histo_save_song_histo(_name, _path, target_path)


def save_index_from_chords(chords_folder,chords_index_folder):
    chord_to_index, index_to_chords = get_chord_dict()
    for path, subdirs, files in os.walk(chords_folder):
        for name in files:
            _path = path.replace('\\', '/') + '/'
            _name = name.replace('\\', '/')
            target_path = chords_index_folder+_path[len(chords_folder):]
            if not os.path.exists(target_path):
                os.makedirs(target_path) 
            mf.chords_to_index_save(_name, _path, target_path, chord_to_index)


def get_chord_dict():
    chord_to_index = pickle.load(open(dict_path + chord_dict_name, 'rb'))
    index_to_chord = pickle.load(open(dict_path + index_dict_name, 'rb'))
    return chord_to_index, index_to_chord


def make_chord_dict(chords_folder, num_chords):
    cntr = count_chords(chords_folder, num_chords)
    chord_to_index = dict()
    chord_to_index[UNK] = 0
    for chord, _ in cntr:
        chord_to_index[chord] = len(chord_to_index)
    index_to_chord = {v: k for k, v in chord_to_index.items()}
    pickle.dump(chord_to_index,open(dict_path + chord_dict_name , 'wb'))
    pickle.dump(index_to_chord,open(dict_path + index_dict_name , 'wb'))
    return chord_to_index, index_to_chord


def count_chords(chords_folder, num_chords):
    chord_cntr = Counter()
    for path, subdirs, files in os.walk(chords_folder):
        for name in files:
            _path = path.replace('\\', '/') + '/'
            _name = name.replace('\\', '/')
            chords = pickle.load(open(_path + _name, 'rb'))
            for chord in chords:
                if chord in chord_cntr:
                    chord_cntr[chord] +=1
                else:
                    chord_cntr[chord] = 1                    
    return chord_cntr.most_common(n=num_chords-1)

def count_chords2(chords_folder, num_chords):
    chord_cntr = Counter()
    for path, subdirs, files in os.walk(chords_folder):
        for name in files:
            _path = path.replace('\\', '/') + '/'
            _path = _path.replace('/shifted', '')
            _name = name.replace('\\', '/')
            chords = pickle.load(open(_path + _name, 'rb'))
            for chord in chords:
                if chord in chord_cntr:
                    chord_cntr[chord] +=1
                else:
                    chord_cntr[chord] = 1                    
    return chord_cntr



def save_chords_from_histo(histo_folder,chords_folder):
    for path, subdirs, files in os.walk(histo_folder):
        for name in files:
            _path = path.replace('\\', '/') + '/'
            _name = name.replace('\\', '/')
            target_path = chords_folder+_path[len(histo_folder):]
            if not os.path.exists(target_path):
                os.makedirs(target_path) 
            mf.load_histo_save_chords(chord_n, _name, _path, target_path)



def save_histo_oct_from_pianoroll_folder():
    #Not Used anymore!!
    for path, subdirs, files in os.walk(pickle_folder):
        for name in files:
            _path = path.replace('\\', '/') + '/'
            _name = name.replace('\\', '/')
            target_path = histo_folder+_path[len(pickle_folder):]
            if not os.path.exists(target_path):
                os.makedirs(target_path) 
            mf.save_pianoroll_to_histo_oct(samples_per_bar,octave, _name, _path, target_path)


def save_histo_oct_from_midi_folder(tempo_folder,histo_folder):
    print(tempo_folder)
    for path, subdirs, files in os.walk(tempo_folder):

        for name in files:
            _path = path.replace('\\', '/') + '/'
            _name = name.replace('\\', '/')
            target_path = histo_folder+_path[len(tempo_folder):]
            if not os.path.exists(target_path):
                os.makedirs(target_path)
            try:
                mf.midi_to_histo_oct(samples_per_bar, octave, fs, _name, _path, target_path)
            except (ValueError, EOFError, IndexError, OSError, KeyError, ZeroDivisionError) as e:
                exception_str = 'Unexpected error in ' + name  + ':\n', e, sys.exc_info()[0]
                print(exception_str)
#                invalid_files_counter +=1



def note_ind_folder(tempo_folder,roll_folder):
    for path, subdirs, files in os.walk(tempo_folder):
        for name in files:
            _path = path.replace('\\', '/') + '/'
            _name = name.replace('\\', '/')
            target_path = roll_folder+_path[len(tempo_folder):]
            if not os.path.exists(target_path):
                os.makedirs(target_path)
            try:
                mf.save_note_ind(_name, _path, target_path, fs)
            except (ValueError, EOFError, IndexError, OSError, KeyError, ZeroDivisionError) as e:
                exception_str = 'Unexpected error in ' + name  + ':\n', e, sys.exc_info()[0]
                print(exception_str)
#                invalid_files_counter +=1


def do_all_steps():
    

    print('changing Tempo')
    # change_tempo_folder(source_folder,tempo_folder1)
    
    print('histogramming')
    # save_histo_oct_from_midi_folder(tempo_folder1,histo_folder1)
   
    print('make song histo')
    # save_song_histo_from_histo(histo_folder1,song_histo_folder)
    
    print('shifting midi files')
    # shift_midi_files(song_histo_folder,tempo_folder1,tempo_folder2)
    
    
    print('making note indexes')
    # note_ind_folder(tempo_folder2,roll_folder)
    
    print('histogramming')
    save_histo_oct_from_midi_folder(tempo_folder2,histo_folder2)
    
    print('extracting chords')
    save_chords_from_histo(histo_folder2,chords_folder)
    
    print('getting dictionary')
    chord_to_index, index_to_chord = make_chord_dict(chords_folder, num_chords)

    print('converting chords to index sequences')
    save_index_from_chords(chords_folder,chords_index_folder)


if __name__=="__main__":
    # do_all_steps()
#    key_counter2 = count_keys()
#    scale_counter2, other_counter2 = count_scales()
#    shift_midi_files()
#    histo = histo_of_all_songs()
#    pickle.dump(histo, open('histo_all_songs.pickle', 'wb'))
#    chord_counter = count_chords(chords_folder, num_chords)
    testttt('/data1/lakh/lmd_matched_processed_ckey_melody_labeled_with_logger_0201')
    print('done')


