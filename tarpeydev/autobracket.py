# import native Python packages
import functools
import random
import datetime
import os

# import third party packages
from flask import Blueprint, render_template, request
from werkzeug.exceptions import BadRequest
import pandas
import numpy
import scipy
from scipy import stats


bp = Blueprint('autobracket', __name__, url_prefix='/autobracket')


@bp.route('/generate', methods=['GET', 'POST'])
def generate():
    return render_template('autobracket/generate.html')


@bp.route('/bracket', methods=['GET', 'POST'])
def bracket():
	# If you go straight to the bracket page, you'll get a 400 error!
	if request.form == {}:
		return 'You should go through the front page!', 400

	# If you try to input non-string objects, you'll get an error!
	# if isinstance(request.form['model_choice'], type('anystring')):
	model_choice = request.form['model_choice']
	# else:
	# 	return 'You didn\'t fill out the form correctly!', 400

	# if isinstance(request.form['chaos_choice'], type('anystring')):
	chaos_choice = int(request.form['chaos_choice'])
	# else:
	# 	return 'You didn\'t fill out the form correctly!', 400

	# if isinstance(request.form['model_current'], type('anystring')):
	model_current = request.form['model_current']
	# else:
	# 	return 'You didn\'t fill out the form correctly!', 400

	# If your chaos_choice is less than 0 or greater than 10, you'll get an error!
	# Otherwise you'll get model results.
	if int(chaos_choice) < 0 or int(chaos_choice) > 10:
		return 'You didn\'t fill out the form correctly!', 400
	else:
		simulated_df, actual_df = run_tournament(
			model_choice,
			chaos_choice,
			model_current,
		)
	# the only thing this is missing is passing through the results...
	return render_template(
		'autobracket/bracket.html',
		simulated_df=simulated_df,
		actual_df=actual_df,
	)


def run_tournament(model_choice, chaos_choice, model_current):
	# pull a clean matchup table for the next model run
	bracket_19 = pandas.read_csv(
        'data/autobracket/matchup_table_2019.csv',
		index_col='game_id',
	)
	# 
	# also pull the actual results, for comparison purposes
	actual_19 = pandas.read_csv(
        'data/autobracket/autobracket_actual_19.csv',
		index_col='game_id',
	)

	# full Kenpom table reads for the classic and modern methods
	kenpom_19 = pandas.read_csv(
		'data/autobracket/team_index_2019.csv',
		index_col='seed',
	)
	kenpom_19_full = pandas.read_csv(
		'data/autobracket/team_index_2019_full.csv',
		index_col='team_id',
	)

	# core of the model. this is the field that will be distributed
	kenpom_19['teamsim'] = kenpom_19['KenTeamAdjO'] / kenpom_19['KenTeamAdjD'] + (kenpom_19['KenTeamOppAdjEM'] / 100)
	kenpom_19_full['teamsim'] = kenpom_19_full['KenTeamAdjO'] / kenpom_19_full['KenTeamAdjD'] + (kenpom_19_full['KenTeamOppAdjEM'] / 100)

	# classic version
	if (model_choice == 'Classic'):
		zmean = kenpom_19['teamsim'].mean()
		zstd = kenpom_19['teamsim'].std(ddof=0)
	# modern version
	else:
		zmean = kenpom_19_full['teamsim'].mean()
		zstd = kenpom_19_full['teamsim'].std(ddof=0)

	# bring in team rating and simulate the game
	x = 1

	# update x if user only wants to run the games that haven't happened yet
	if (model_current == 'partial'):
		bracket_19 = pandas.read_csv(
			'data/autobracket/autobracket_actual_19.csv',
			index_col='game_id'
		)
		x = x + 4 + 32 + 16 #+ 8 + 4 + 2 + 1

	while x < 68:
		# lookup values for seed1, seed2
		z1 = bracket_19.loc[x, 'seed1']
		z2 = bracket_19.loc[x, 'seed2']

		# identifying the advancing location in bracket
		z3 = bracket_19.loc[x, 'advance_to']

		# populate games (z-sim uniform method)
		bracket_19.loc[x, 'team1sim'] = random.uniform(
			scipy.stats.norm.cdf((kenpom_19.loc[str(z1), 'teamsim'] - zmean) / zstd) * (10 - chaos_choice), 10
		)
		bracket_19.loc[x, 'team2sim'] = random.uniform(
			scipy.stats.norm.cdf((kenpom_19.loc[str(z2), 'teamsim'] - zmean) / zstd) * (10 - chaos_choice), 10
		)

		# who won?
		w_team = numpy.where(
			bracket_19.loc[x, 'team1sim'] > bracket_19.loc[x, 'team2sim'],
			bracket_19.loc[x, 'team1'],
			bracket_19.loc[x, 'team2']
		)
		w_seed = numpy.where(
			bracket_19.loc[x, 'team1sim'] > bracket_19.loc[x, 'team2sim'],
			bracket_19.loc[x, 'seed1'],
			bracket_19.loc[x, 'seed2']
		)

		# if the team1 slot is full, need to fill the team2 slot instead
		f1 = numpy.where(
			pandas.isna(bracket_19.loc[z3,'team1']),
			'team1',
			'team2'
		)
		f2 = numpy.where(
			pandas.isna(bracket_19.loc[z3,'team1']),
			'seed1',
			'seed2'
		)
		
		# advance the correct team/seed to the correct slot
		bracket_19.loc[z3, str(f1)] = str(w_team)
		bracket_19.loc[z3, str(f2)] = str(w_seed)

		x = x + 1

	# output modeled bracket to database.
	# step removed

	if(str(bracket_19.loc[x-1, 'team1']) == str(w_team)):
		winner = 'team1'
	else:
		winner = 'team2'

	champion_19 = pandas.DataFrame(
		{
			'champion':[bracket_19.loc[x-1, winner]],
			'timestamp':datetime.datetime.now(),
			'model_choice':model_choice,
			'modelChaos':chaos_choice,
			'modelSize':model_current,
		}
	)
	
	# output champion to champion table in database
	# step removed

	return(bracket_19, actual_19)
