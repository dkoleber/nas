from __future__ import annotations
import sys
import numpy as np
from scipy import stats

from EvolutionStrategy import AgingStrategy
from FitnessCalculator import AccuracyCalculator
from Dataset import ImageDataset
import matplotlib.pyplot as plt
import time
from FileManagement import *
from Modelv3 import *
from SerialData import SerialData
from Hyperparameters import Hyperparameters

HERE = os.path.dirname(os.path.abspath(__file__))

import tensorflow as tf


def test_accuracy_at_different_train_amounts_2():
    dir_path = os.path.join(evo_dir, 'test_accuracy_epochs')
    sims = [x for x in os.listdir(dir_path) if '.png' not in x]
    full_sims = [x for x in sims if 'small' not in x]
    small_sims = [x for x in sims if 'small' in x]
    todo_small_sims = full_sims[len(small_sims):]

    print(f'{len(todo_small_sims)} remaining small sims to conduct')

    population = [MetaModel.load(dir_path, x, False) for x in todo_small_sims]

    adjusted_normal_stacks = 3
    adjusted_layer_stacks = 2

    dataset = ImageDataset.get_cifar10()

    for x in population:
        x.hyperparameters.parameters['NORMAL_CELL_N'] = adjusted_normal_stacks
        x.hyperparameters.parameters['CELL_LAYERS'] = adjusted_layer_stacks
        x.metrics.metrics['accuracy'] = []
        x.metrics.metrics['average_train_time'] = []
        x.metrics.metrics['average_inference_time'] = []
        x.model_name = 'evo_small_' + str(time.time())
        x.build_model(dataset.images_shape)
        x.evaluate(dataset)
        x.save_model(dir_path)
        x.save_metadata(dir_path)
        x.clear_model()


def test_accuracy_at_different_train_amounts_analyze():
    population = []

    dir_path = f'{evo_dir}\\test_accuracy_epochs'
    folders = [x for x in os.listdir(dir_path) if '.png' not in x and 'small' not in x]
    for candidate in folders:
        loaded = MetaModel.load(dir_path, candidate, False)
        population.append(loaded)

    x = []
    y = []
    c = []

    x_multi = []
    y_multi = []
    c_multi = []

    fitnesses = [[] for i in range(len(population[0].metrics.metrics['accuracy']))]

    color = 0
    for index, candidate in enumerate(population):
        x_temp = []
        y_temp = []
        for round in range(len(candidate.metrics.metrics['accuracy'])):
            fitness = candidate.metrics.metrics['accuracy'][round]
            x.append(index)
            y.append(fitness)
            c.append(color + round)

            x_temp.append(round)
            y_temp.append(fitness)

            fitnesses[round].append(fitness)
        # print(len(candidate.metrics.metrics['accuracy']))

        x_multi.append(x_temp)
        y_multi.append(y_temp)
        color = (1. / len(population)) * float(index)
        c_multi.append((color, color, color))

    final_fitness_coorelation = [np.corrcoef(i, fitnesses[-1])[0][1] for i in fitnesses]
    initial_fitness_coorelation = [np.corrcoef(i, fitnesses[0])[0][1] for i in fitnesses]

    area = np.pi * 8

    num_plots = 4

    # plt.figure(dpi=80)

    fig, axes = plt.subplots(nrows=num_plots, ncols=1)


    plt.subplot(num_plots, 1, 1)
    plt.scatter(x, y, c=c, s=area, alpha=0.5)
    plt.title('candidate vs fitness')
    plt.xlabel('candidate')
    plt.ylabel('fitness')

    plt.subplot(num_plots, 1, 2)
    for i in range(len(x_multi)):
        plt.plot(x_multi[i], y_multi[i], c=c_multi[i], alpha=0.5)

    plt.title('epoch vs fitness')
    plt.xlabel('epoch')
    plt.ylabel('fitness')

    plt.subplot(num_plots, 1, 3)
    plt.plot([i for i in range(len(final_fitness_coorelation))], final_fitness_coorelation, alpha=0.5)
    plt.title('accuracy at epoch coorelation with final accuracy')
    plt.xlabel('epoch')
    plt.ylabel('coorelation coefficient')

    plt.subplot(num_plots, 1, 4)
    plt.plot([i for i in range(len(initial_fitness_coorelation))], initial_fitness_coorelation, alpha=0.5)
    plt.title('accuracy at epoch coorelation with initial accuracy')
    plt.xlabel('epoch')
    plt.ylabel('coorelation coefficient')

    # fig.tight_layout()
    # plt.subplots_adjust(hspace=3.0)

    plt.savefig(os.path.join(dir_path, 'figure.png'))
    # plt.show()


def test_accuracy_at_different_train_amounts_analyze_2():
    large_population_models = []
    small_population_models = []

    dir_path = f'{evo_dir}\\test_accuracy_epochs'
    folders = [x for x in os.listdir(dir_path) if '.png' not in x]
    for candidate in folders:
        loaded = MetaModel.load(dir_path, candidate, False)
        if 'small' in candidate:
            small_population_models.append(loaded)
        else:
            large_population_models.append(loaded)

    small_accuracies = [x.metrics.metrics['accuracy'] for x in small_population_models]
    large_accuracies = [x.metrics.metrics['accuracy'] for x in large_population_models][:len(small_accuracies)]


    num_iterations = len(large_accuracies[0])
    num_models = len(large_accuracies)

    z_large_accuracies = stats.zscore(large_accuracies, axis=0)
    z_small_accuracies = stats.zscore(small_accuracies, axis=0)
    final_z_large = [x[-1] for x in z_large_accuracies]
    final_z_small = [x[-1] for x in z_small_accuracies]

    indexes = np.array([x for x in range(num_models)])
    accuracy_correlation = [np.corrcoef(z_large_accuracies[i], z_small_accuracies[i])[0][1] for i in range(num_models)]

    iterations = np.array([x for x in range(num_iterations)])
    se_at_iterations = np.power(np.subtract(z_large_accuracies, z_small_accuracies),2)
    mse_at_iterations = np.average(se_at_iterations, axis=0)
    vals = np.polyfit(iterations, mse_at_iterations, 1)

    area = np.pi * 8
    num_plots = 2
    plt.subplot(num_plots, 1, 1)
    plt.scatter(indexes, accuracy_correlation, c=indexes, s=area, alpha=0.5)
    plt.title('candidate vs fitness')
    plt.xlabel('candidate')
    plt.ylabel('small vs large accuracy correlation')

    plt.subplot(num_plots, 1, 2)
    plt.scatter(iterations, mse_at_iterations, c=iterations, s=area, alpha=0.5)
    plt.plot(iterations, iterations * vals[0] + vals[1])
    plt.title('iteration vs mse zvals at iterations')
    plt.xlabel('iteration')
    plt.ylabel('mse zval')

    plt.savefig(os.path.join(dir_path, 'small_vs_large.png'))

    print(f'accuracy correlation mean across candidates: {np.average(accuracy_correlation)}')
    print(f'accuracy correlation stdev across candidates: {np.std(accuracy_correlation)}')
    print(f'accuracy correlation max across candidates: {max(accuracy_correlation)}')
    print(f'accuracy correlation min across candidates: {min(accuracy_correlation)}')
    print(f'final accuracy correlation among all candidates: {np.corrcoef(final_z_large, final_z_small)[0][1]}')
    print(f'correlation between iteration and mse zval: {np.corrcoef(iterations, mse_at_iterations)[0][1]}')


def test_model_mutation():
    init_dir_path = os.path.join(evo_dir, 'test_accuracy_epochs_h5')
    dataset = ImageDataset.get_cifar10()
    dir_path = os.path.join(evo_dir, 'test_mutation_accuracy')

    if not os.path.exists(dir_path):
        os.makedirs(dir_path)

    parent_samples = [x for x in os.listdir(init_dir_path) if 'small' not in x and 'png' not in x]
    init_samples = parent_samples[:8]
    init_samples.extend(parent_samples[-8:]) # use the first 8 and the last 8, since the first half has different hyperparameters than the second half //TODO: USE SMALLER MODELS?

    done_seeded_samples = [x for x in os.listdir(dir_path) if '_seeded' in x]
    done_fresh_samples = [x for x in os.listdir(dir_path) if '_fresh' in x]

    remaining_seeded_samples = [x for x in init_samples if x + '_seeded' not in done_seeded_samples]
    remaining_fresh_samples = [x for x in init_samples if x + '_fresh' not in done_fresh_samples]

    print(f'{len(remaining_seeded_samples)} seeded samples remaining (of {len(init_samples)})')
    print(f'{len(remaining_fresh_samples)} fresh samples remaining (of {len(init_samples)})')
    print(f'{len(init_samples)} total samples to process')

    def set_parameters(model):
        parent_model.metrics.metrics['accuracy'] = []
        parent_model.metrics.metrics['average_train_time'] = []
        parent_model.metrics.metrics['average_inference_time'] = []
        parent_model.hyperparameters.parameters['TRAIN_ITERATIONS'] = 1

    for index, parent in enumerate(init_samples):
        tf.keras.backend.clear_session()
        parent_model = None

        if parent in remaining_seeded_samples:
            parent_model = MetaModel.load(init_dir_path, parent, True)
            print(f'training {index} from parent weights')
            set_parameters(parent_model)
            parent_model.model_name = parent + '_seeded'
            pre_accuracy = float(parent_model.keras_model.evaluate(dataset.test_images, dataset.test_labels)[-1])
            parent_model.apply_mutation(1, 0, 1, .99, 1. / float(OperationType.SEP_7X7))
            post_accuracy = float(parent_model.keras_model.evaluate(dataset.test_images, dataset.test_labels)[-1])
            # print(f'accuracy pre training post mutation: {pre_accuracy}')
            parent_model.metrics.metrics['accuracy'].append(pre_accuracy)
            parent_model.metrics.metrics['accuracy'].append(post_accuracy)
            parent_model.evaluate(dataset)
            parent_model.save_model(dir_path)
            parent_model.save_metadata(dir_path)
            parent_model.clear_model()
        if parent in remaining_fresh_samples and False:
            print(f'training {index} without parent weights')
            set_parameters(parent_model)
            parent_model.build_model(dataset.images_shape)
            parent_model.model_name = parent + '_fresh'
            parent_model.evaluate(dataset)
            parent_model.save_model(dir_path)
            parent_model.save_metadata(dir_path)
            parent_model.clear_model()
