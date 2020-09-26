# import native Python packages
import base64
import functools
import io
import json
import os

# import third party packages
from flask import Blueprint, render_template, request
import numpy
import pandas
import plotly
import plotly.express as px
import plotly.figure_factory as ff
import plotly.graph_objects as go

# import custom local stuff
from tarpeydev.plotly_style import tarpeydev_default, tarpeydev_black


ml_bp = Blueprint('mildredleague', __name__, url_prefix='/mildredleague')


@ml_bp.route('/', methods=['GET', 'POST'])
@ml_bp.route('/home', methods=['GET', 'POST'])
def home():
    return render_template(
        'mildredleague/home.html',
    )


@ml_bp.route('/alltime', methods=['GET', 'POST'])
def alltime():
    # grab charts
    all_time_rankings_json = all_time_ranking_fig()
    all_time_matchups_json = matchup_heatmap_fig()
    all_time_wins_json = all_time_wins_fig()
    
    return render_template(
        'mildredleague/alltime.html',
        ranks=all_time_rankings_json,
        matchups=all_time_matchups_json,
        wins=all_time_wins_json,
    )


@ml_bp.route('/<year>', methods=['GET', 'POST'])
def season(year):
    # pull boxplot score data for the season. True=against, False=for
    boxplot_json_for = season_boxplot(year, False)
    boxplot_json_against = season_boxplot(year, True)
    notes = season_notes(year)
    table = season_table(year)

    return render_template(
        'mildredleague/season.html',
        boxplot_for=boxplot_json_for,
        boxplot_against=boxplot_json_against,
        notes=notes,
        table=table,
        season=year,
    )


@ml_bp.route('/rules', methods=['GET', 'POST'])
def rules():
    return render_template(
        'mildredleague/rules.html',
    )


def season_notes(year):
    # dictionary of notes on each page
    notes = {
        '2013': [
            '2013 was the inaugural year of Mildred League. Brando was technically running the league at this point with Tarpey as co-commissioner.',
            'The original name of the league was "El Futbol Drafto", and the championship game was still known as the "Drafto Bowl".',
            'Bryant\'s 0-13 record this year stood as the worst regular season in league history until 2018, when Mildred\'s Redskins posted an 0-14 regular season record.',
            'In the four-team playoff, Tarpey edged a 218-214 win over Brando in the semifinals and went on to upset the #1 seed Christian in the finals.',
        ],
        '2014': [
            'The 2014 season marked the beginning of the "Winners Get Wings" tradition in Mildred League (Arthur\'s team name). For the next 5 seasons, the champion received a $25 gift card (sometimes BWW, sometimes cash...or in Brando\'s case I just bought him dinner).',
            'The league expanded to 12 teams, but still had a clear top cut for the second year in a row. Four teams went 10-3 and made playoffs. The next best record was 7-5.',
            'At 1,240 points for in the regular season, Brando had the rightful claim to the title and proceeded to win both of his playoff games handily.',
        ],
        '2015': [
            'Another expansion in 2015 resulted in a 14-team league (which was initially met with some protest).',
            '2015 was a tale of two divisions. East Coast Bias finished the season with 5 teams within 1.5 games of each other. The half-game was Conti\'s doing. His tie with Matt in week 2 ended up being the division winner for him.',
            'None of what happened in ECB mattered though, because the new champ would come from the West. Fonti went 11-2 in the regular season and blew out both of his playoff matchups.',
            'This was the beginning of a string of heartbreaks for both Samik (2nd) and Conti (3rd).',
        ],
        '2016': [
            'By 2016 the league had scaled back to 12 teams and was largely run through a Facebook group.',
            'This season marked a complete fall from grace for Tarpey: after winning the inaugural season, he finished dead last this year.',
            'Division record tiebreakers had not yet been implemented, so Points For ended up deciding the three-way tie at 9-4 for the #2/#3/#4 seeds. In a heartbreaker, Fonti (8-5) finished one game out of playoffs and missed out on his chance to be the only back-to-back champion.',
            'A competitive two-week final between Frank and Conti resulted in Frank\'s first championship. The heartbreakers for Conti (2nd) and Samik (4th) continued.',
        ],
        '2017': [
            'Year 5 of Mildred League gave birth to the modern divisional format, somewhat inspired by MLB (3 divisions of 5/5/4 teams). The goal was to place more emphasis on divisional rivalries and winning the division - this has largely been successful!',
            'Fonti won the Champions division handily, but the other two divisions were much more competitive. Sendzik edged out the AFC East by one game, and Charles did the same in the Referees division.',
            'Brando did the commissioner a favor and avoided tiebreaker hell by securing the only wild card spot (despite an extremely low Points For total for the season). Just behind him, FOUR other teams finished at 7-6...',
            'Fonti got revenge for his playoff miss in 2016 and became the first repeat champion.',
        ],
        '2018': [
            'The prior season revealed that the new three-division format could work, but it needed an equivalent playoff overhaul. In 2018 the playoffs were expanded to 6 teams (3 division winners and 3 wild cards) and tiebreakers were overhauled to put more emphasis on winning divisional games.',
            'The regular season was expanded to 14 games to accomodate three playoff rounds (and playoff matchups were shortened to one game instead of two).',
            'The consolation bracket was also overhauled into a Swiss tournament, where the 3-0 team would receive their choice of draft order in the next season.',
            'The Champions and AFC East divisions had clear cut winners (Samik in particular seemed poised to finally break through with a record Points For total).',
            'The playoffs were chaos (see the bracket below). The only chalk was Tarpey winning his second title. Every other matchup was a seeding upset.',
            'Conti (2nd) and Samik (4th) once again came up just short of a title. =[',
            'After a mostly-Washington draft, Mildred\'s Redskins set the record for the worst regular season performance of all time at 0-14.',
        ],
        '2019': [
            'Arguably the most competitive season to date, Mildred League VII was the first to use non-traditional rosters [QB/RB/2WR/TE/2FLX/1K/1D/5B]. Moving an RB to FLX was aimed at better reflecting the modern NFL and providing teams with more flexibility in such a deep league. Shortening the bench was aimed at increasing comeback potential for teams behind in the standings (better waiver opportunities).',
            'This was also the first money league season ($20 entry).',
            'Comeback story of the year belonged to Mildred, who turned an 0-14 year into 9-5 and a division win + playoff berth.',
            'Tiebreaker hell was once again narrowly averted after Brad\'s last week choke cleared the way for Conti to take yet another shot at the title. (At one point, a five-way tie for the last playoff spot was possible...)',
            'After winning the consolation bracket in 2018, Frank made his first pick draft slot count and claimed a first-round bye, then defeated Tarpey in the semifinals. However, in the finals Frank cleared the way for Sendzik\'s first title!',
        ],
    }
    return notes[year]


def season_table(year):
    # pull all games and filter for the season
    season_games_df = all_games()
    season_games_df = season_games_df.loc[season_games_df.season == int(year)]
    season_records_df = calc_records(
        season_games_df
    ).reset_index()
    # pull all rankings and filter for the season
    season_ranking_df = all_time_ranking()
    season_ranking_df = season_ranking_df.loc[season_ranking_df.year == int(year)]
    # merge playoff ranking and active status
    season_records_df = season_records_df.merge(
        season_ranking_df[['nick_name', 'playoff_rank', 'active']],
        on='nick_name',
        how='left',
    ).sort_values(
        by='playoff_rank', ascending=True
    )

    return season_records_df


def all_games():
    # read each season's summary of games
    season_files = [
        'mlgames2013.csv',
        'mlgames2014.csv',
        'mlgames2015.csv',
        'mlgames2016.csv',
        'mlgames2017.csv',
        'mlgames2018.csv',
        'mlgames2019.csv',
    ]

    # empty dataframe for all games
    all_games_df = pandas.DataFrame()

    # for each CSV, append to the all games dataframe
    for season_file in season_files:
        # file path construction
        season_path = os.path.join(
            os.getcwd(),
            'data',
            'mildredleague',
            season_file
        )
        # read season file
        season_df = pandas.read_csv(
            season_path,
        )
        if all_games_df.empty is True:
            all_games_df = season_df
        else:
            all_games_df = all_games_df.append(
                season_df,
                ignore_index=True,
            )

    # fix datatypes
    all_games_df = all_games_df.convert_dtypes()

    # which team won?
    all_games_df['a_win'] = 0
    all_games_df['h_win'] = 0
    all_games_df['a_tie'] = 0
    all_games_df['h_tie'] = 0
    # away win
    all_games_df.loc[all_games_df.a_score > all_games_df.h_score, 'a_win'] = 1
    # home win
    all_games_df.loc[all_games_df.a_score < all_games_df.h_score, 'h_win'] = 1
    # tie
    all_games_df.loc[all_games_df.a_score == all_games_df.h_score, ['a_tie', 'h_tie']] = 1
    # normalized score columns for two-week playoff games
    all_games_df['a_score_norm'] = (
        all_games_df['a_score'] / (
            all_games_df['week_e'] - all_games_df['week_s'] + 1
        )
    )
    all_games_df['h_score_norm'] = (
        all_games_df['h_score'] / (
            all_games_df['week_e'] - all_games_df['week_s'] + 1
        )
    )
    # margin = home - away
    all_games_df['h_margin'] = all_games_df['h_score_norm'] - all_games_df['a_score_norm'] 

    return all_games_df


def calc_records(games_df):
    # season wins for away teams, home teams
    away_wins_for_df = pandas.pivot_table(games_df, values='a_win', index='a_nick', aggfunc='sum', fill_value=0)
    home_wins_for_df = pandas.pivot_table(games_df, values='h_win', index='h_nick', aggfunc='sum', fill_value=0)
    # season losses for away teams, home teams
    away_losses_for_df = pandas.pivot_table(games_df, values='h_win', index='a_nick', aggfunc='sum', fill_value=0)
    home_losses_for_df = pandas.pivot_table(games_df, values='a_win', index='h_nick', aggfunc='sum', fill_value=0)
    away_losses_for_df.rename(columns={'h_win': 'a_loss'}, inplace=True)
    home_losses_for_df.rename(columns={'a_win': 'h_loss'}, inplace=True)
    # ties
    away_ties_df = pandas.pivot_table(games_df, values='a_tie', index='a_nick', aggfunc='sum', fill_value=0)
    home_ties_df = pandas.pivot_table(games_df, values='h_tie', index='h_nick', aggfunc='sum', fill_value=0)
    # season points for for away teams, home teams
    away_points_for_df = pandas.pivot_table(games_df, values='a_score_norm', index='a_nick', aggfunc='sum', fill_value=0)
    home_points_for_df = pandas.pivot_table(games_df, values='h_score_norm', index='h_nick', aggfunc='sum', fill_value=0)
    # season points against for away teams, home teams
    away_points_against_df = pandas.pivot_table(games_df, values='h_score_norm', index='a_nick', aggfunc='sum', fill_value=0)
    home_points_against_df = pandas.pivot_table(games_df, values='a_score_norm', index='h_nick', aggfunc='sum', fill_value=0)
    away_points_against_df.rename(columns={'h_score_norm': 'a_score_norm_against'}, inplace=True)
    home_points_against_df.rename(columns={'a_score_norm': 'h_score_norm_against'}, inplace=True)
    # merge to one table
    record_df = home_wins_for_df.join(
        [
            away_wins_for_df,
            home_losses_for_df,
            away_losses_for_df,
            home_ties_df,
            away_ties_df,
            home_points_for_df,
            away_points_for_df,
            home_points_against_df,
            away_points_against_df,
         ],
         how='inner',
    ).rename_axis('nick_name')
    # win total, loss total, game total, points for, points against, win percentage
    record_df['win_total'] = record_df['h_win'] + record_df['a_win']
    record_df['loss_total'] = record_df['h_loss'] + record_df['a_loss']
    record_df['tie_total'] = record_df['h_tie'] + record_df['a_tie']
    record_df['games_played'] = record_df['win_total'] + record_df['loss_total'] + record_df['tie_total']
    record_df['win_pct'] = (record_df['win_total'] + record_df['tie_total'] * 0.5) / record_df['games_played']
    record_df['points_for'] = record_df['h_score_norm'] + record_df['a_score_norm']
    record_df['points_against'] = record_df['h_score_norm_against'] + record_df['a_score_norm_against']
    record_df['avg_margin'] = (record_df['points_for'] - record_df['points_against']) / record_df['games_played']
    record_df.sort_values(by='win_total', ascending=True, inplace=True)
    record_df.drop(
        columns=[
            'h_win',
            'a_win',
            'h_loss',
            'a_loss',
            'h_tie',
            'a_tie',
            'h_score_norm',
            'a_score_norm',
            'h_score_norm_against',
            'a_score_norm_against',
        ],
        inplace=True,
    )

    return record_df


def calc_matchup_records(games_df):
    # grouping for away and home matchup winners
    away_wins_df = pandas.pivot_table(games_df, values='a_win', index=['a_nick', 'h_nick'], aggfunc='sum', fill_value=0)
    home_wins_df = pandas.pivot_table(games_df, values='h_win', index=['h_nick', 'a_nick'], aggfunc='sum', fill_value=0)
    # ties. only need to do this once since both teams receive a tie in a tie row
    away_ties_df = pandas.pivot_table(games_df, values='a_tie', index=['a_nick', 'h_nick'], aggfunc='sum', fill_value=0)
    home_ties_df = pandas.pivot_table(games_df, values='h_tie', index=['h_nick', 'a_nick'], aggfunc='sum', fill_value=0)
    # grouping for away and home matchup OCCURRENCES
    away_games_df = pandas.pivot_table(
        games_df, values='season', index=['a_nick', 'h_nick'], aggfunc='count', fill_value=0
    ).rename(columns={'season': 'a_games'})
    home_games_df = pandas.pivot_table(
        games_df, values='season', index=['h_nick', 'a_nick'], aggfunc='count', fill_value=0
    ).rename(columns={'season': 'h_games'})
    # rename indices
    away_wins_df.index.set_names(names=['winner', 'loser'], inplace=True)
    home_wins_df.index.set_names(names=['winner', 'loser'], inplace=True)
    away_ties_df.index.set_names(names=['winner', 'loser'], inplace=True)
    home_ties_df.index.set_names(names=['winner', 'loser'], inplace=True)
    away_games_df.index.set_names(names=['winner', 'loser'], inplace=True)
    home_games_df.index.set_names(names=['winner', 'loser'], inplace=True)
    # join and sum to get total matchup wins
    matchup_df = away_wins_df.join(
        [home_wins_df, away_ties_df, home_ties_df],
        how='outer',
    ).fillna(0).convert_dtypes()
    # ties count for 0.5
    matchup_df['win_total'] = (
        matchup_df['a_win'] +
        matchup_df['h_win'] +
        matchup_df['a_tie'] * 0.5 +
        matchup_df['h_tie'] * 0.5
    )
    # merge and sum to get total matchup occurrences
    total_matchup_df = away_games_df.join(
        [home_games_df],
        how='outer',
    ).fillna(0).convert_dtypes()
    total_matchup_df['game_total'] = total_matchup_df.sum(axis=1)
    # get rid of intermediate columns. just wins and games now
    matchup_df = matchup_df.join(
        total_matchup_df,
        how='outer',
    ).convert_dtypes().drop(
        columns=[
            'a_win',
            'h_win',
            'a_tie',
            'h_tie',
            'a_games',
            'h_games',
        ]
    )
    # add win pct column
    matchup_df['win_pct'] = matchup_df['win_total'] / matchup_df['game_total']

    return matchup_df


def all_time_wins_fig():
    # pull all games ever
    all_games_df = all_games()
    # regular season df
    regular_df = all_games_df.loc[all_games_df.playoff == 0]
    # convert to record_df
    record_df = calc_records(
        regular_df
    ).reset_index().sort_values('win_total', ascending=True)

    figure = px.bar(
        record_df,
        x='win_total',
        y='nick_name',
        orientation='h',
        color='nick_name',
        template=tarpeydev_default(),
    )

    # generic bar chart so we can use our custom colors
    # instead of using plotly express
    figure = go.Figure()
    figure.update_layout(
        title="Regular Season Win Totals",
        margin=dict(l=120, r=60),
        xaxis=dict(
            title=None,
        ),
        yaxis=dict(
            title=None,
        ),
        showlegend=False,
        hovermode='closest',
        template=tarpeydev_default(),
    )
    # now convert the data to lists and add one at a time
    # to attach different colors in the cycle
    xy = record_df[['win_total', 'nick_name']].values.tolist()
    
    for i, bar in enumerate(xy):
        figure.add_trace(
            go.Bar(
                x=[xy[i][0]],
                y=[xy[i][1]],
                orientation='h',
                name=xy[i][1],
            )
        )

    figure_json = json.dumps(figure, cls=plotly.utils.PlotlyJSONEncoder)

    return figure_json


def all_time_ranking():
    # file path construction
    all_time_path = os.path.join(
        os.getcwd(),
        'data',
        'mildredleague',
        'mlalltime.csv'
    )
    # read season file
    ranking_df = pandas.read_csv(
        all_time_path,
    )

    return ranking_df


def all_time_ranking_fig():
    # data pull
    ranking_df = all_time_ranking()

    # pivot by year for all teams
    annual_ranking_df = pandas.pivot(
        ranking_df,
        index='nick_name',
        columns='year',
        values='playoff_rank'
    )

    # temporary variable to rank relevance of a team.
    # higher numbers are less relevant.
    # 15 for teams that didn't play in a given year
    # (worst rank for a team that existed would be 14)
    annual_ranking_df_temp = annual_ranking_df.fillna(15)
    annual_ranking_df_temp['relevance'] = annual_ranking_df_temp.sum(axis=1)
    annual_ranking_df['relevance'] = annual_ranking_df_temp['relevance']
    annual_ranking_df.sort_values(by='relevance', ascending=False, inplace=True)
    annual_ranking_df.reset_index(inplace=True)

    # y axis labels
    nick_names = annual_ranking_df.nick_name.to_list()

    # drop unnecessary columns
    annual_ranking_df.drop(columns=['nick_name', 'relevance'], inplace=True)

    # x axis labels
    seasons = annual_ranking_df.columns.tolist()

    # need to pull out of data frame format for this particular figure
    annual_ranking_list = annual_ranking_df.values.tolist()
    
    # need a separate set for the annotations to look good
    ranking_annotations = annual_ranking_df.values.tolist()

    # convert to Int64 and blanks for the actual annotations
    for i, player in enumerate(ranking_annotations):
        for j, annual_result in enumerate(player):
            if numpy.isnan(annual_result):
                ranking_annotations[i][j] = ''
            else:
                ranking_annotations[i][j] = int(annual_result)

    # set up the figure and its axes
    figure = ff.create_annotated_heatmap(
        annual_ranking_list,
        x=seasons,
        y=nick_names,
        annotation_text=ranking_annotations,
        # subset of px.colors.sequential.Blues
        colorscale=[
            'rgb(107,174,214)',
            'rgb(66,146,198)',
            'rgb(33,113,181)',
            'rgb(8,81,156)',
            'rgb(8,48,107)',
        ],
    )

    # update margins and colors
    figure.update_layout(
        title="Mildred League Placements by Season",
        template=tarpeydev_black(),
        margin=dict(l=120, r=60),
    )
    figure.update_xaxes(showgrid=False, showline=False)
    figure.update_yaxes(showgrid=False, showline=False)

    # convert to JSON for the web
    figure_json = json.dumps(figure, cls=plotly.utils.PlotlyJSONEncoder)

    return figure_json


def matchup_heatmap_fig():
    # pull all games ever
    all_games_df = all_games()
    # convert to record_df
    matchup_df = calc_matchup_records(
        all_games_df
    ).reset_index()
    # pull all-time file to filter active teams
    ranking_df = all_time_ranking()

    # game total custom data for the hover text
    game_df = matchup_df.merge(
        ranking_df.loc[
            ranking_df.active == 1,
            ['nick_name']
        ].drop_duplicates(),
        left_on='winner',
        right_on='nick_name',
        how='inner',
    ).merge(
        ranking_df.loc[
            ranking_df.active == 1,
            ['nick_name']
        ].drop_duplicates(),
        left_on='loser',
        right_on='nick_name',
        how='inner',
    ).drop(
        columns=['nick_name_x', 'nick_name_y']
    ).set_index(keys=['winner', 'loser'])[['game_total']].unstack()

    # inner join will result in only active teams. unstack
    matchup_df = matchup_df.merge(
        ranking_df.loc[
            ranking_df.active == 1,
            ['nick_name']
        ].drop_duplicates(),
        left_on='winner',
        right_on='nick_name',
        how='inner',
    ).merge(
        ranking_df.loc[
            ranking_df.active == 1,
            ['nick_name']
        ].drop_duplicates(),
        left_on='loser',
        right_on='nick_name',
        how='inner',
    ).drop(
        columns=['nick_name_x', 'nick_name_y']
    ).set_index(keys=['winner', 'loser'])[['win_pct']].unstack()

    # start creating the figure!
    # y axis labels
    winners = matchup_df.index.to_list()
    # x axis labels
    opponents = matchup_df.columns.get_level_values(1).to_list()
    figure = go.Figure(
        data=go.Heatmap(
            z=matchup_df[['win_pct']],
            customdata=game_df[['game_total']],
            hovertemplate='Winner: %{y}<br>Opponent: %{x}<br>Win %: %{z:.3f}<br>Games: %{customdata} <extra></extra>',
            x=opponents,
            y=winners,
            colorscale=plotly.colors.diverging.Tropic,
        )
    )

    # update margins and colors
    figure.update_layout(
        title="Matchup Win Percentage (Active Teams)",
        template=tarpeydev_default(),
        margin=dict(l=120, r=60, t=150, autoexpand=True),
        # custom xaxis and yaxis titles
    )
    figure.update_xaxes(showgrid=False, showline=False, side='top', ticks='')
    figure.update_yaxes(showgrid=False, showline=False, ticks='')

    figure_json = json.dumps(figure, cls=plotly.utils.PlotlyJSONEncoder)

    return figure_json


def season_boxplot(year, against=True):
    # read the selected season as a dataframe
    season_path = os.path.join(
        os.getcwd(),
        'data',
        'mildredleague',
        'mlgames' + str(year) + '.csv',
    )
    # read season file
    season_df = pandas.read_csv(
        season_path,
    )
    # normalized score columns for two-week playoff games
    season_df['a_score_norm'] = (
        season_df['a_score'] / (
            season_df['week_e'] - season_df['week_s'] + 1
        )
    )
    season_df['h_score_norm'] = (
        season_df['h_score'] / (
            season_df['week_e'] - season_df['week_s'] + 1
        )
    )
    # we just want unique scores. so let's stack away and home.
    # this code runs to analyze Points For.
    if against is False:
        score_df = season_df[['a_nick', 'a_score_norm']].rename(
            columns={'a_nick': 'name', 'a_score_norm': 'score'},
        ).append(
            season_df[['h_nick', 'h_score_norm']].rename(
                columns={'h_nick': 'name', 'h_score_norm': 'score'},
            ),
            ignore_index=True,
        )
        title_label='(Points For)'
    # this code runs to analyze Points Against.
    if against is True:
        score_df = season_df[['a_nick', 'h_score_norm']].rename(
            columns={'a_nick': 'name', 'h_score_norm': 'score'},
        ).append(
            season_df[['h_nick', 'a_score_norm']].rename(
                columns={'h_nick': 'name', 'a_score_norm': 'score'},
            ),
            ignore_index=True,
        )
        title_label='(Points Against)'
    # let's sort by playoff rank instead
    all_time_path = os.path.join(
        os.getcwd(),
        'data',
        'mildredleague',
        'mlalltime.csv'
    )
    # read season file, but we only need nick_name, year, and playoff_rank
    ranking_df = pandas.read_csv(
        all_time_path,
    )[['nick_name', 'year', 'playoff_rank']]
    # merge this (filtered by year) into score_df so we can sort values
    score_df = score_df.merge(
        ranking_df.loc[ranking_df.year == int(year), ['nick_name', 'playoff_rank']],
        left_on=['name'],
        right_on=['nick_name'],
        how='left',
    ).sort_values(
        by='playoff_rank', ascending=True,
    )

    # plotly boxplot!
    figure = px.box(
        score_df,
        x="name",
        y="score",
        color="name",
        color_discrete_sequence=px.colors.qualitative.Light24,
        points="all",
        title=year + " Scores " + title_label,
        template=tarpeydev_default()
    )

    # turn off names at the bottom
    figure.update_xaxes(showticklabels=False)

    # update margins and colors
    figure.update_layout(
        xaxis_title=None,
        margin=dict(l=70, r=50, t=60, b=30),
        legend=dict(
            orientation='h',
            y=0,
            xanchor='left',
            x=0,
        ),
    )

    # convert to JSON for the web
    figure_json = json.dumps(figure, cls=plotly.utils.PlotlyJSONEncoder)

    return figure_json

