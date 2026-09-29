/**
* Name: PD
* Based on the internal skeleton template.
* Author: szydzi7681
* Tags:
*/

model PD

global {
	/** Insert the global definitions, variables and actions here */
	file park_boundary_shapefile <- file("../includes/gis/drogi.geojson");
	file park_paths_shapefile <- file("../includes/gis/drogi.geojson");
	graph path_network;

	bool real_env <- true;
	bool unlimited_games <- false;

	bool show_social_links <- true;
	float social_link_threshold <- 0.3;

	int nb_game <- 0;
	map<string, game> active_pairs <- [];

	list<string> characters <- ["TFT","QLEARN","AQLEARN","ALLC","ALLD","FTFT","TF2T","GRIM","WSLS"];
	list<string> character_pool;

	int nb_QLEARN <- 0;
	int nb_AQLEARN <- 0;
	int nb_TFT <- 0;
	int nb_ALLC <- 0;
	int nb_ALLD <- 0;
	int nb_FTFT <- 0;
	int nb_TF2T <- 0;
	int nb_GRIM <- 0;
	int nb_WSLS <- 0;

	float env_influence_qlearn <- 0.0;
	float social_sensitivity_aqlearn <- 0.0;
	float social_learning_boost_aqlearn <- 0.0;
	float movement_sensitivity <- 2.0;
	float broken_windows_sensitivity <- 0.0;
	float disorder_bump_dd <- 0.15;   // obopólna, jawna defekcja - mocniejszy sygnał
	float disorder_bump_d <- 0.08;    // pojedyncza defekcja
	float disorder_decay <- 0.98;
	int generalization_threshold <- 3;

	string base_character_qlearn <- "TFT";
	float character_strength_qlearn <- 0.0;
	float anchor_decay_rate <- 0.15;  // wykładniczy zanik kotwicy - ustaliliśmy, że lepiej pasuje do "punktu krytycznego" niż harmoniczny

	float disorder_bump_for(string m1, string m2) {
	    if m1 = "D" and m2 = "D" { return disorder_bump_dd; }
	    if m1 = "D" or m2 = "D" { return disorder_bump_d; }
	    return 0.0;
	}

	float recent_defection_rate(int window) {
	    list<string> recent_moves <- [];
	    loop p over: player {
	        loop lst over: p.my_moves_per_other.values {
	            recent_moves <- recent_moves + last(min(window, length(lst)), lst);
	        }
	    }
	    if empty(recent_moves) { return 0.0; }
	    int d_count <- length(recent_moves where (each = "D"));
	    return d_count / length(recent_moves);
	}

	int end_cycle <- 50000;
	string variant_name <- "unset";
	bool log_games <- true;  // zapis każdej gry do konsoli i PD.csv - wyłączane w batchach

	int vision_radius <- 10;
	int world_size <- 10;

	geometry shape <- real_env ? envelope(park_boundary_shapefile) : square(world_size);

	int payoff_R <- 5;
	int payoff_P <- 1;
	int payoff_T <- 9;
	int payoff_S <- 0;

	int grid_cols <- 50;
	int grid_rows <- 50;
	float cell_learning_rate <- 0.1;

	int selected_index <- 0;

	player selected_player() {
		list<player> all_players <- list(player);
		if empty(all_players) {
			return nil;
		}
		int idx <- min(selected_index, length(all_players) - 1);
		return all_players[idx];
	}

	float feedback_value(string my_move, string opp_move) {
		if my_move = "C" and opp_move = "C" {
			return 0.1;
		}
		if my_move = "D" and opp_move = "D" {
			return -0.8;
		}
		if my_move = "D" and opp_move = "C" {
			return 1.0;
		}
		if my_move = "C" and opp_move = "D" {
			return -1.0;
		}
		return 0.0;
	}

	float average_feedback(environment_cell cell) {
		list<float> values <- [];
		loop p over: player {
			if cell in p.personal_feedback.keys {
				values <+ p.personal_feedback[cell];
			}
		}
		return empty(values) ? 0.0 : mean(values);
	}

	float normalized_visual_height(player p) {
		list<float> values <- player collect each.for_chart;

		if empty(values) {
			return 0.0;
		}

		float v_min <- min(values);
		float v_max <- max(values);

		if v_max = v_min {
			return 0.0;
		}

		return 10 * (p.for_chart - v_min) / (v_max - v_min);
	}

	float mean_for(string ch) {
		list<player> group <- player where (each.character = ch and each.nb_games > 0);
		if empty(group) {
			return 0.0;
		}
		return mean(group collect (each.score / each.nb_games * 1000));
	}

	float mean_score_all() {
		list<player> group <- player where (each.nb_games > 0);
		if empty(group) {
			return 0.0;
		}
		return mean(group collect (each.score / each.nb_games * 1000));
	}

	float mean_for_classic() {
		list<string> classic <- ["TFT", "ALLC", "ALLD", "FTFT", "TF2T", "GRIM", "WSLS"];
		list<player> group <- player where (each.nb_games > 0 and (each.character in classic));
		if empty(group) {
			return 0.0;
		}
		return mean(group collect (each.score / each.nb_games * 1000));
	}

	float aqlearn_clique_fraction() {
		list<player> aq <- player where (each.character = "AQLEARN");
		int total <- 0;
		int high <- 0;
		loop p over: aq {
			loop q over: aq {
				if p!= q {
					total <- total + 1;
					float v <- (q in p.social_feedback.keys) ? p.social_feedback[q] : 0.0;
					if v > 0.5 {
						high <- high + 1;
					}
				}
			}
		}
		return total = 0 ? 0.0 : (high / total);
	}

	float aqlearn_avg_distance() {
		list<player> aq <- player where (each.character = "AQLEARN");
		if length(aq) < 2 {
			return 0.0;
		}
		list<float> dists <- [];
		loop i from: 0 to: length(aq) - 1 {
			loop j from: i + 1 to: length(aq) - 1 {
				dists <+ (aq[i].location distance_to aq[j].location);
			}
		}
		return mean(dists);
	}

	reflex export_metrics when: cycle = end_cycle {
		save [
			variant_name,
			mean_score_all(),
			mean_for("QLEARN"),
			mean_for("AQLEARN"),
			mean_for_classic(),
			aqlearn_clique_fraction(),
			aqlearn_avg_distance()
		] to: "../results/ablation_results.csv" rewrite: false format: "csv" header: true;
	}

	string pair_key(player a, player b) {
		return (a.name < b.name) ? (a.name + "|" + b.name) : (b.name + "|" + a.name);
	}

	init {
		if not (payoff_T > payoff_R and payoff_R > payoff_P and payoff_P > payoff_S) {
			error "Niepoprawna macierz wypłat: wymagane T > R > P > S.
Aktualnie : T=" + payoff_T + " R=" + payoff_R + " P=" + payoff_P + " S=" + payoff_S;
		}
		if not (2 * payoff_R > payoff_T + payoff_S) {
			write "OSTRZEŻENIE: 2R <= T+S (" + (2*payoff_R) + " <= " + (payoff_T + payoff_S) + ")
- naprzemienna eksploatacja nie jest gorsza niż stała kooperacja.";
		}

		create park_boundary from: park_boundary_shapefile;
		create path_segment from: park_paths_shapefile;
		path_network <- as_edge_graph(path_segment);

		map<string,int> counts <- [
			"QLEARN"::nb_QLEARN,
			"AQLEARN"::nb_AQLEARN,
			"TFT"::nb_TFT,
			"ALLC"::nb_ALLC,
			"ALLD"::nb_ALLD,
			"FTFT"::nb_FTFT,
			"TF2T"::nb_TF2T,
			"GRIM"::nb_GRIM,
			"WSLS"::nb_WSLS
		];

		loop k over: counts.keys {
			loop times: counts[k] {
				character_pool <+ k;
			}
		}
		if not empty(character_pool){
			loop i from: 0 to: length(character_pool) - 1 {
				create player {
					character <- character_pool[i];
					do apply_character_params();
					do setup_lists();
					if real_env {
						do init_on_network();
					}
				}
			}
		}
	}
}

species park_boundary {
	aspect default {
		draw shape color: #forestgreen border: #darkgreen ;
	}
}

grid environment_cell width: grid_cols height: grid_rows neighbors: 8 {

	float disorder <- 0.0;

	reflex decay_disorder when: every(10) {
	    do apply_decay();
	}

	action apply_decay() {
		disorder <- disorder * disorder_decay;
	}

	rgb summary_color() {
		float fb <- world.average_feedback(self);
		if fb > 0 {
			return rgb(255 * (1 - fb), 255, 255 * (1 - fb));
		} else if fb < 0 {
			return rgb(255, 255 * (1 + fb), 255 * (1 + fb));
		}
		return #white;
	}

	rgb personal_color(player p) {
		if p = nil {
			return #white;
		}
		float fb <- (self in p.personal_feedback.keys) ? p.personal_feedback[self] : 0.0;
		if fb > 0 {
			return rgb(255 * (1 - fb), 255, 255 * (1 - fb));
		} else if fb < 0 {
			return rgb(255, 255 * (1 + fb), 255 * (1 + fb));
		}
		return #white;
	}
	aspect summary {
		draw shape color: summary_color();
	}
	aspect personal {
		draw shape color: personal_color(world.selected_player());
	}
	aspect default {
		draw shape color: #white border: #lightgrey;
	}
}

species path_segment {
	aspect default {
		draw shape color: #sienna width: 2;
	}
}

species game{
	string pair_key;
	player p1;
	player p2;
	string p1_move;
	string p2_move;
	int lifespan <- 10;


	init {
		nb_game <- nb_game + 1;
		p1_move <- p1.strategy(p2);
		p2_move <- p2.strategy(p1);
		// THS IS SETTELED p1.move;
		player opponent_of_p1 <- p2;
		player opponent_of_p2 <- p1;

		float fb_p1 <- world.feedback_value(p1_move, p2_move);
		float fb_p2 <- world.feedback_value(p2_move, p1_move);

		environment_cell cell_p1 <- environment_cell(p1.location);
		environment_cell cell_p2 <- environment_cell(p2.location);

		ask p1 {
			do update_personal_feedback(cell_p1, fb_p1);
			do update_social_feedback(opponent_of_p1, fb_p1);
			if myself.p2_move = "D" { do register_betrayal(cell_p1); }
		}

		ask p2 {
			do update_personal_feedback(cell_p2, fb_p2);
			do update_social_feedback(opponent_of_p2, fb_p2);
			if myself.p1_move = "D" { do register_betrayal(cell_p2); }
		}

		int p1_payoff <- 0;
		int p2_payoff <- 0;


		if p1_move = "D" and p2_move = "D" {
			p2_payoff <- payoff_P;
			p1_payoff <- payoff_P;

		} else if p1_move = "C" and p2_move = "C" {
			p2_payoff <- payoff_R;
			p1_payoff <- payoff_R;

		} else if p1_move = "D" and p2_move = "C" {
			p2_payoff <- payoff_S;
			p1_payoff <- payoff_T;

		} else if p1_move = "C" and p2_move = "D" {
			p2_payoff <- payoff_T;
			p1_payoff <- payoff_S;
		}

		float bump <- world.disorder_bump_for(p1_move, p2_move);
		if bump > 0 {
		    ask cell_p1 { disorder <- disorder + bump; }
		    if cell_p2 != cell_p1 {
		        ask cell_p2 { disorder <- disorder + bump; }
		    }
		}

		if unlimited_games {
			p2.score <- p2.score + p2_payoff;
			p1.score <- p1.score + p1_payoff;
		} else {
			p2.height <- p2.height + p2_payoff;
			p1.height <- p1.height + p1_payoff;
		}

		p2.lists_per_other[p1] <+ p1_move;
		p2.my_moves_per_other[p1] <+ p2_move;

		p1.lists_per_other[p2] <+ p2_move;
		p1.my_moves_per_other[p2] <+ p1_move;

		p1.nb_games <- p1.nb_games + 1;
		p2.nb_games <- p2.nb_games + 1;

		if p1.character = "QLEARN" or p1.character = "AQLEARN"{
			int payoff_of_p1 <- p1_payoff;
			ask p1 {
				do update_q(opponent_of_p1, payoff_of_p1);
			}
		}

		if p2.character = "QLEARN" or p2.character = "AQLEARN"{
			int payoff_of_p2 <- p2_payoff;
			ask p2 {
				do update_q(opponent_of_p2, payoff_of_p2);
			}
		}

//		write "cycle[" + cycle + "] Gra między " + p2 + " i " + p1 + ".
//		p2 move: " + p2_move + ". p1 move: " + p1_move + ".
//		p2 score: " + p2.score + ". p1 score: " + p1.score + ".";

		if log_games {
			write "" + nb_game + "," + cycle + "," + p1 + "," + p2 + "," + p1_move + "," + p2_move + "," + p1.score + "," + p2.score;
			save [nb_game,cycle,p1,p2,p1_move,p2_move,p1.score,p2.score]
				rewrite: false to: "../results/PD.csv" format: "csv" header: true;
		}
    }


	reflex die{
		lifespan <- lifespan - 1;
		if lifespan = 0{
			remove key: pair_key from: world.active_pairs;
			do die();
		}
	}

	aspect default{
		draw circle(5) color: #red;
	}
}

species player skills: [moving] {

	int height <- 0;
	int score <- 0;
	float for_chart -> nb_games > 0 ? (score / nb_games * 1000) : 0.0;
	list<player> close -> player at_distance(vision_radius);
	string character;
	player enemy;
	float forgiveness  <- 0.05;
	int nb_games;

	point current_node;
	point target_node;
	float move_speed <- 2.0;
	float sensitivity <- 2.0;

	map<player, float> social_feedback;
	float social_learning_rate <- 0.1;
	float social_sensitivity <- 0.0;
	float social_learning_boost <- 0.0;
	float env_influence <- 0.0;
	float initial_cooperation_bias <- min(1.0, max(0.0, gauss(0.5, 0.15)));

	string base_character <- "TFT";
	float character_strength <- 0.0;
	map<environment_cell, int> betrayal_count_at_location;

	// parametry zależne od charakteru - wydzielone z global.init, żeby dało się je testować
	action apply_character_params() {
		sensitivity <- movement_sensitivity;
		if character = "AQLEARN" {
			social_sensitivity <- social_sensitivity_aqlearn;
			social_learning_boost <- social_learning_boost_aqlearn;
		}
		if character = "QLEARN" or character = "AQLEARN" {
			env_influence <- env_influence_qlearn;
			base_character <- base_character_qlearn;
			character_strength <- character_strength_qlearn;
		}
	}

	action register_betrayal(environment_cell cell) {
	    if cell = nil { return; }
	    int old_val <- (cell in betrayal_count_at_location.keys) ? betrayal_count_at_location[cell] : 0;
	    betrayal_count_at_location[cell] <- old_val + 1;
	}

	string get_state(player p) {
	    string base_state;
	    if lists_per_other[p] = [] {
	        base_state <- "START";
	    } else {
	        base_state <- last(my_moves_per_other[p]) + "|" + last(lists_per_other[p]);
	    }
	    environment_cell here <- environment_cell(location);
	    bool risky <- (here != nil)
	        and (here in betrayal_count_at_location.keys)
	        and (betrayal_count_at_location[here] >= generalization_threshold);
	    return base_state + "|" + (risky ? "RISKY" : "SAFE");
	}

	string character_suggested_move(player p) {
		if base_character = "TFT" { return TFT(p); }
		else if base_character = "ALLC" { return ALLC(p); }
		else if base_character = "ALLD" { return ALLD(p); }
		else if base_character = "FTFT" { return FTFT(p); }
		else if base_character = "TF2T" { return TF2T(p); }
		else if base_character = "GRIM" { return GRIM(p); }
		else if base_character = "WSLS" { return WSLS(p); }
		else { return "C"; }
	}

	float effective_anchor_strength(player p) {
		int n <- length(lists_per_other[p]);
		float base <- character_strength * exp(-anchor_decay_rate * n);
		environment_cell here <- environment_cell(location);
		float erosion <- (here != nil) ? (1 - broken_windows_sensitivity * here.disorder) : 1.0;
		erosion <- max(0.0, erosion);
		return max(0.0, min(1.0, base * erosion));
	}

	action init_on_network() {
		current_node <- path_network.vertices closest_to self;
		location <- current_node;
	}

	point weighted_next_node(list<point> candidates) {
		map<point, float> weights <- map<point, float>([]);
		loop c over: candidates {
			environment_cell cell <- environment_cell(c);
			float fb <- (cell != nil and cell in personal_feedback.keys) ? personal_feedback[cell] : 0.0;
			float social <- social_sensitivity > 0 ? social_score(c) : 0.0;
			weights[c] <- exp(sensitivity * fb + social_sensitivity * social);
		}
		return rnd_choice(weights);
	}

	reflex choose_target when: real_env and (target_node = nil or location = target_node) {
		list<point> neighbors <- list(path_network neighbors_of current_node);
		if empty(neighbors) {
			target_node <- current_node;
		} else {
			target_node <- weighted_next_node(neighbors);
			current_node <- target_node;
		}
	}

	reflex move_on_network when: real_env and target_node != nil and location != target_node {
		do goto (target:target_node, on:path_network, speed:move_speed);
	}

	reflex wander_fallback when: !real_env {
		do wander(amplitude:90.0);
	}

	reflex height_decay when: !unlimited_games {
		if height > 0 {
			height <- height - 1;
			score <- score + 1;
		}
	}

	map<environment_cell, float> personal_feedback;

	action update_personal_feedback(environment_cell cell, float value) {
		if cell = nil {
			return;
		}
		float old_val <- (cell in personal_feedback.keys) ? personal_feedback[cell] : 0.0;
		personal_feedback[cell] <- old_val + cell_learning_rate * (value - old_val);
	}

	action update_social_feedback(player opponent, float value) {
		float old_val <- (opponent in social_feedback.keys) ? social_feedback[opponent] : 0.0;
		social_feedback[opponent] <- old_val + social_learning_rate * (value - old_val);
	}

	float social_score(point candidate) {
		float s_s <- 0.0;
		loop p over: social_feedback.keys {
			float pref <- social_feedback[p];
			float dist_now <- current_node distance_to p.location;
			float dist_candidate <- candidate distance_to p.location;
			float normalized_delta <- (dist_now - dist_candidate) / max(1.0, move_speed);
			s_s <- s_s + pref * normalized_delta;
		}
		return s_s / max(1, length(social_feedback));
	}

	map<player, list<string>> lists_per_other;
	map<player, list<string>> my_moves_per_other;

	map<player, map<string, float>> q_d_per_other;
	map<player, map<string, float>> q_c_per_other;
	map<player, string> pending_state;
	map<player, string> pending_action;

	float learning_rate <- 0.1;
	float discount <- 0.9;
	float epsilon <- 0.15;

	action setup_lists() {
		ask player where (each != self) {
			myself.lists_per_other[self] <- [];
			myself.my_moves_per_other[self] <- [];
			myself.q_d_per_other[self] <- map<string, float>([]);
			myself.q_c_per_other[self] <- map<string, float>([]);

			self.lists_per_other[myself] <- [];
			self.my_moves_per_other[myself] <- [];
			self.q_d_per_other[myself] <- map<string, float>([]);
			self.q_c_per_other[myself] <- map<string, float>([]);
		}
	}

	// nowy stan zawsze startuje z priorem initial_cooperation_bias - niezależnie od tego,
	// czy pierwszy raz pojawia się w QLEARN, czy jako next_s w update_q
	action ensure_q_state(player opponent, string s) {
		if not (s in q_d_per_other[opponent].keys) {
			q_d_per_other[opponent][s] <- (1 - initial_cooperation_bias);
			q_c_per_other[opponent][s] <- initial_cooperation_bias;
		}
	}

	action update_q(player opponent, int reward) {
		string s <- pending_state[opponent];
		string a <- pending_action[opponent];

		float old_q <- (a = "D") ? q_d_per_other[opponent][s] : q_c_per_other[opponent][s];

		string next_s <- get_state(opponent);
		do ensure_q_state(opponent, next_s);

		float max_next_q <- max(q_d_per_other[opponent][next_s], q_c_per_other[opponent][next_s]);

		float social_pref <- (opponent in social_feedback.keys) ? social_feedback[opponent] : 0.0;
		float effective_lr <- learning_rate * (1 + social_learning_boost * social_pref);
		effective_lr <- max(0.01, min(0.99, effective_lr));

		float new_q <- old_q + effective_lr * (reward + discount * max_next_q - old_q);

		if a = "D" {
			q_d_per_other[opponent][s] <- new_q;
		} else {
			q_c_per_other[opponent][s] <- new_q;
		}
	}

//	reflex debug_qtable when: character = "QLEARN" and every(50) {
//		write name + " Q-table snapshot:";
//		loop p over: q_c_per_other.keys {
//			loop s over: q_c_per_other[p].keys {
//				write "  vs " + p.name + " state=" + s + " D=" + q_c_per_other[p][s] + " C=" + q_d_per_other[p][s];
//			}
//		}
//	}

//	string get_state(player p) {
//		if lists_per_other[p] = [] {
//			return "START";
//		}
//		string my_last <- last(my_moves_per_other[p]);
//		string opp_last <- last(lists_per_other[p]);
//		return my_last + "|" + opp_last;
//	}

	string strategy(player p) {
		if not unlimited_games and height != 0 { return nil; }
		string base_move;
		if character = "TFT" { base_move <- TFT(p); }
		else if character = "ALLC" { base_move <- ALLC(p); }
		else if character = "ALLD" { base_move <- ALLD(p); }
		else if character = "FTFT" { base_move <- FTFT(p); }
		else if character = "TF2T" { base_move <- TF2T(p); }
		else if character = "GRIM" { base_move <- GRIM(p); }
		else if character = "WSLS" { base_move <- WSLS(p); }
		else if character = "QLEARN" or character = "AQLEARN" { base_move <- QLEARN(p); }
		else { error "Nieznany charakter: " + character; }

		if base_move = "C" and broken_windows_sensitivity > 0 {
		    environment_cell here <- environment_cell(location);
		    float local_disorder <- (here != nil) ? here.disorder : 0.0;
		    if flip(min(0.9, broken_windows_sensitivity * local_disorder)) {
		        base_move <- "D";
		    }
		}

		if (character = "QLEARN" or character = "AQLEARN") and (p in pending_action.keys) {
		    pending_action[p] <- base_move;   // domknięcie: pending_action = to, co naprawdę zagrano
		}

		return base_move;
	}



//	string strategy(player p) {
//		if not unlimited_games and height != 0 {
//			return nil;
//		}
//		if character = "TFT" {
//			return TFT(p);
//		} else if character = "ALLC" {
//			return ALLC(p);
//		} else if character = "ALLD" {
//			return ALLD(p);
//		} else if character = "FTFT" {
//			return FTFT(p);
//		} else if character = "TF2T" {
//			return TF2T(p);
//		} else if character = "GRIM" {
//			return GRIM(p);
//		} else if character = "WSLS" {
//			return WSLS(p);
//		} else if character = "QLEARN" or character = "AQLEARN"{
//			return QLEARN(p);
//		} else {
//			error "Nieznany charakter: " + character;
//		}
//	}

	string TFT(player p) {
		if lists_per_other[p] = [] {
			return flip(0.5) ? "C" : "D";
		}
		if last(lists_per_other[p]) = "C" {
			return "C";
		}
		return "D";
	}

	string ALLD(player p) {
		return "D";
	}

	string ALLC(player p) {
		return "C";
	}

	string FTFT(player p) {
		if lists_per_other[p] = [] {
			return "C";
		}
		if last(lists_per_other[p]) = "C" {
			return "C";
		}
		if last(lists_per_other[p]) = "D" and flip(forgiveness){
			return "C";
		}
		return "D";
	}

	string TF2T(player p) {
		if lists_per_other[p] = [] {
			return flip(0.5) ? "C" : "D";
		}
		if last(2, lists_per_other[p]) != ["D","D"] {
			return "C";
		}
		return "D";
	}

	string GRIM(player p) {
		if lists_per_other[p] contains "D"{
			return "D";
		}
		return "C";
	}

	string WSLS(player p) {
		if lists_per_other[p] = [] {
			return flip(0.5) ? "C" : "D";
		}
		string my_last <- last(my_moves_per_other[p]);
		string enemy_last <- last(lists_per_other[p]);

		if enemy_last = "C" {
			return my_last;
		}
		return (my_last = "C") ? "D" : "C";
	}

	string QLEARN(player p) {
		string s <- get_state(p);
		do ensure_q_state(p, s);

		environment_cell here <- environment_cell(location);
		float env_fb <- (here != nil and here in personal_feedback.keys) ? personal_feedback[here] : 0.0;

		float adjusted_q_d <- q_d_per_other[p][s] - env_influence * env_fb;
		float adjusted_q_c <- q_c_per_other[p][s] + env_influence * env_fb;

		string action_chosen;
		if flip(epsilon) {
			action_chosen <- flip(0.5) ? "D" : "C";
		} else if adjusted_q_d = adjusted_q_c {
			action_chosen <- flip(0.5) ? "D" : "C";   // remis rozstrzygany losowo, nie na korzyść D
		} else {
			action_chosen <- (adjusted_q_d > adjusted_q_c) ? "D" : "C";
		}

		if character_strength > 0 {
			float pull <- effective_anchor_strength(p);
			if flip(pull) {
				action_chosen <- character_suggested_move(p);
			}
		}

		pending_state[p] <- s;
		pending_action[p] <- action_chosen;

		return action_chosen;
	}

	reflex do_you_wanna_play when: !empty(close - self) and (unlimited_games or height = 0) {

		enemy <- one_of(close - [self]);

		if enemy != nil and (unlimited_games or enemy.height = 0) {

			player a <- self;
			player b <- enemy;

			string key <- world.pair_key(a,b);

			if !(key in world.active_pairs.keys) {
				point pn1 <- self.location;
				point pn2 <- enemy.location;

				create game(p1:a,p2:b,location:(pn1 + pn2) / 2, pair_key:key) returns: new_games;

				world.active_pairs[key] <- first(new_games);
			}
		}
	}

	rgb social_link_color(float v) {
		if v > 0 {
			return rgb(0, 255 * min(1.0, v), 0);
		} else {
			return rgb(255 * min(1.0, -v), 0, 0);
		}
	}

	action draw_own_social_links() {
		list<player> candidates <- social_feedback.keys where (abs(social_feedback[each]) > social_link_threshold);
		list<player> sorted_candidates <- candidates sort_by (-abs(social_feedback[each]));
		list<player> top <- first(3, sorted_candidates);

		loop p over: top {
			float v <- social_feedback[p];
			draw line([location, p.location]) color: social_link_color(v) width: 1 + 3 * abs(v);
		}
	}

	aspect social_links_all {
		if show_social_links {
			do draw_own_social_links();
		}
	}

	aspect social_links_selected {
		if show_social_links and self = world.selected_player() {
			do draw_own_social_links();
		}
	}

	aspect cone{
		draw cylinder(10, world.normalized_visual_height(self)) color: (self = world.selected_player() ? #blue : #black);
	}
}

experiment PD type: gui {
	/** Insert here the definition of the input and output of the model */
	parameter "Wybrany agent (indeks)" var: selected_index min: 0 category: "Podgląd pamięci";
	parameter "Pokaż linie relacji społecznych" var: show_social_links category: "Podgląd pamięci";
	parameter "Próg rysowania linii" var: social_link_threshold category: "Podgląd pamięci";

	parameter "Ilość agentów QLEARN" var: nb_QLEARN min: 0 category: "Ilości agentów";
	parameter "Ilość agentów AQLEARN" var: nb_AQLEARN min: 0 category: "Ilości agentów";
	parameter "Ilość agentów TFT" var: nb_TFT min: 0 category: "Ilości agentów";
	parameter "Ilość agentów FTFT" var: nb_FTFT min: 0 category: "Ilości agentów";
	parameter "Ilość agentów TF2T" var: nb_TF2T min: 0 category: "Ilości agentów";
	parameter "Ilość agentów GRIM" var: nb_GRIM min: 0 category: "Ilości agentów";
	parameter "Ilość agentów ALLC" var: nb_ALLC min: 0 category: "Ilości agentów";
	parameter "Ilość agentów ALLD" var: nb_ALLD min: 0 category: "Ilości agentów";
	parameter "Ilość agentów WSLS" var: nb_WSLS min: 0 category: "Ilości agentów";

	parameter "Prawdziwe środowisko" var: real_env category: "Środowisko";
	parameter "Ograniczenie rozgrywania gier" var: unlimited_games category: "Środowisko";
	parameter "Rozmiar świata (działa przy sztucznym środowisku)" var: world_size min: 0 category: "Środowisko";
	parameter "Kolumny siatki" var: grid_cols min: 0 category: "Środowisko";
	parameter "Wiersze siatki" var: grid_rows min: 0 category: "Środowisko";
	parameter "Zasięg widzenia" var: vision_radius category: "Środowisko";
	parameter "Czułość ruchu (środowisko)" var: movement_sensitivity category: "Środowisko";
	parameter "Wpływ środowiska na decyzję QLEARN" var: env_influence_qlearn category: "Środowisko";
	parameter "Czułość społeczna AQLEARN" var: social_sensitivity_aqlearn category: "Środowisko";
	parameter "Wzmocnienie uczenia społecznego AQLEARN" var: social_learning_boost_aqlearn category: "Środowisko";

	output {
		display abc {
			species environment_cell aspect: summary;
			species park_boundary aspect: default transparency: 0.3;
			species path_segment aspect: default;
			species player aspect: social_links_all;
			species player aspect: cone;

			//species game aspect: default;
		}
		display chart type: 2d{
			chart "Score" type: series{
				loop p_s over: player{
					data "" + p_s + p_s.character + " score" value: p_s.for_chart;
				}
			}
		}
		display agent_memory {
			species environment_cell aspect: personal;
			species park_boundary aspect: default transparency: 0.3;
			species path_segment aspect: default;
			species player aspect: social_links_selected;
			species player aspect: cone;


			overlay position: {10, 10} size: {250 #px, 40 #px} background: #white transparency: 0.3 {
				draw "Agent #" + string(selected_index) +
					(world.selected_player() != nil ? " (" + world.selected_player().character + ")" : "")
					at: {10#px, 20#px} color: #black font: font("Arial", 12, #bold);

			}
		}
	}
}

experiment A_baseline type: batch repeat: 30 until: cycle > end_cycle keep_seed: false {
	parameter "variant_name" var: variant_name init: "A_baseline";
	parameter "log_games" var: log_games init: false;
	parameter "Ilość agentów QLEARN" var: nb_QLEARN init: 20;
	parameter "Ilość agentów AQLEARN" var: nb_AQLEARN init: 0;
	parameter "movement_sensitivity" var: movement_sensitivity init: 0.0;
	parameter "env_influence_qlearn" var: env_influence_qlearn init: 0.0;
	parameter "social_sensitivity_aqlearn" var: social_sensitivity_aqlearn init: 0.0;
	parameter "social_learning_boost_aqlearn" var: social_learning_boost_aqlearn init: 0.0;
}

experiment B_env_movement type: batch repeat: 30 until: cycle > end_cycle keep_seed: false {
	parameter "variant_name" var: variant_name init: "B_env_movement";
	parameter "log_games" var: log_games init: false;
	parameter "Ilość agentów QLEARN" var: nb_QLEARN init: 20;
	parameter "Ilość agentów AQLEARN" var: nb_AQLEARN init: 0;
	parameter "movement_sensitivity" var: movement_sensitivity init: 2.0;
	parameter "env_influence_qlearn" var: env_influence_qlearn init: 0.0;
	parameter "social_sensitivity_aqlearn" var: social_sensitivity_aqlearn init: 0.0;
	parameter "social_learning_boost_aqlearn" var: social_learning_boost_aqlearn init: 0.0;
}

experiment C_social_movement type: batch repeat: 30 until: cycle > end_cycle keep_seed: false {
	parameter "variant_name" var: variant_name init: "C_social_movement";
	parameter "log_games" var: log_games init: false;
	parameter "Ilość agentów QLEARN" var: nb_QLEARN init: 0;
	parameter "Ilość agentów AQLEARN" var: nb_AQLEARN init: 20;
	parameter "movement_sensitivity" var: movement_sensitivity init: 2.0;
	parameter "env_influence_qlearn" var: env_influence_qlearn init: 0.0;
	parameter "social_sensitivity_aqlearn" var: social_sensitivity_aqlearn init: 1.5;
	parameter "social_learning_boost_aqlearn" var: social_learning_boost_aqlearn init: 0.0;
}

experiment D_social_learning type: batch repeat: 30 until: cycle > end_cycle keep_seed: false {
	parameter "variant_name" var: variant_name init: "D_social_learning";
	parameter "log_games" var: log_games init: false;
	parameter "Ilość agentów QLEARN" var: nb_QLEARN init: 0;
	parameter "Ilość agentów AQLEARN" var: nb_AQLEARN init: 20;
	parameter "movement_sensitivity" var: movement_sensitivity init: 2.0;
	parameter "env_influence_qlearn" var: env_influence_qlearn init: 0.0;
	parameter "social_sensitivity_aqlearn" var: social_sensitivity_aqlearn init: 1.5;
	parameter "social_learning_boost_aqlearn" var: social_learning_boost_aqlearn init: 2.0;
}

experiment E1_classic_TFT type: batch repeat: 30 until: cycle > end_cycle keep_seed: false {
    parameter "variant_name" var: variant_name init: "E1_classic_TFT";
    parameter "log_games" var: log_games init: false;
    parameter "Ilość agentów TFT" var: nb_TFT init: 20;
    parameter "movement_sensitivity" var: movement_sensitivity init: 2.0;
}

experiment E2_classic_WSLS type: batch repeat: 30 until: cycle > end_cycle keep_seed: false {
    parameter "variant_name" var: variant_name init: "E2_classic_WSLS";
    parameter "log_games" var: log_games init: false;
    parameter "Ilość agentów WSLS" var: nb_WSLS init: 20;
    parameter "movement_sensitivity" var: movement_sensitivity init: 2.0;
}

experiment E3_classic_GRIM type: batch repeat: 30 until: cycle > end_cycle keep_seed: false {
    parameter "variant_name" var: variant_name init: "E3_classic_GRIM";
    parameter "log_games" var: log_games init: false;
    parameter "Ilość agentów GRIM" var: nb_GRIM init: 20;
    parameter "movement_sensitivity" var: movement_sensitivity init: 2.0;
}

experiment F_broken_windows_anchor type: batch repeat: 30 until: cycle > end_cycle keep_seed: false {
	parameter "variant_name" var: variant_name init: "F_broken_windows_anchor";
	parameter "log_games" var: log_games init: false;
	parameter "Ilość agentów AQLEARN" var: nb_AQLEARN init: 20;
	parameter "movement_sensitivity" var: movement_sensitivity init: 2.0;
	parameter "social_sensitivity_aqlearn" var: social_sensitivity_aqlearn init: 1.5;
	parameter "social_learning_boost_aqlearn" var: social_learning_boost_aqlearn init: 2.0;
	parameter "broken_windows_sensitivity" var: broken_windows_sensitivity init: 0.4;
	parameter "base_character_qlearn" var: base_character_qlearn init: "TFT";
	parameter "character_strength_qlearn" var: character_strength_qlearn init: 0.6;
}

experiment test_disorder_decay type: test {
    test "disorder zanika geometrycznie z disorder_decay" {
        environment_cell c <- first(environment_cell);
        ask c { disorder <- 1.0; }
        loop times: 10 {
            ask c { do apply_decay(); }
        }
        float expected <- 1.0 * (disorder_decay ^ 10);
        assert abs(c.disorder - expected) < 0.001;
    }
}

experiment test_disorder_bump_asymmetry type: test {
    test "D-D podbija disorder mocniej niż D-C, C-C nie podbija wcale" {
        // disorder_bump_for jest tą samą funkcją, której używa game.init
        assert world.disorder_bump_for("D", "D") = disorder_bump_dd;
        assert world.disorder_bump_for("D", "C") = disorder_bump_d;
        assert world.disorder_bump_for("C", "D") = disorder_bump_d;
        assert world.disorder_bump_for("C", "C") = 0.0;
        assert world.disorder_bump_for("D", "D") > world.disorder_bump_for("D", "C");
    }
}

experiment test_broken_windows_affects_classic type: test {
    test "ALLC defektuje częściej przy wysokim disorder niż przy zerowym" {
        broken_windows_sensitivity <- 0.5;
        create player(character:"ALLC") number: 1;
        player p <- first(player);
        environment_cell here <- environment_cell(p.location);

        ask here { disorder <- 0.0; }
        int d_count_low <- 0;
        loop times: 1000 { if p.strategy(p) = "D" { d_count_low <- d_count_low + 1; } }

        ask here { disorder <- 1.0; }
        int d_count_high <- 0;
        loop times: 1000 { if p.strategy(p) = "D" { d_count_high <- d_count_high + 1; } }

        assert d_count_low = 0; // ALLC bez disorder nigdy nie defektuje
        assert d_count_high > 400; // przy disorder=1.0, sensitivity=0.5 -> ~50% D
    }
}

experiment test_reputation_state_dimension type: test {
    test "get_state zwraca RISKY dopiero po przekroczeniu progu" {
        generalization_threshold <- 3;
        create player number: 2;
        player p <- player[0];
        player opp <- player[1];
        ask p { do setup_lists(); }
        environment_cell here <- environment_cell(p.location);

        assert (p.get_state(opp) contains "SAFE");

        ask p { do register_betrayal(here); } // 1
        assert (p.get_state(opp) contains "SAFE");

        ask p { do register_betrayal(here); } // 2
        assert (p.get_state(opp) contains "SAFE");

        ask p { do register_betrayal(here); } // 3 = próg
        assert (p.get_state(opp) contains "RISKY");
    }
}

experiment test_anchor_decay type: test {
    test "effective_anchor_strength maleje wykładniczo z liczbą interakcji" {
        broken_windows_sensitivity <- 0.0; // wyłącz erozję środowiskową na czas testu
        anchor_decay_rate <- 0.15;
        create player(character:"QLEARN", character_strength:0.8) number: 2;
        player p <- player[0];
        player opp <- player[1];
        ask p { do setup_lists(); }

        float s0 <- p.effective_anchor_strength(opp); // n=0
        assert abs(s0 - 0.8) < 0.001; // exp(0) = 1, brak erozji -> pełna siła

        loop times: 5 { p.lists_per_other[opp] <+ "C"; } // symuluj 5 interakcji
        float s5 <- p.effective_anchor_strength(opp);
        float expected <- 0.8 * exp(-0.15 * 5);
        assert abs(s5 - expected) < 0.001;
        assert s5 < s0; // musi maleć
    }
}

experiment test_anchor_erosion_by_disorder type: test {
    test "wysoki disorder obniża effective_anchor_strength do zera" {
        anchor_decay_rate <- 0.0;
        create player(character:"QLEARN", character_strength:0.8) number: 2;
        player p <- player[0];
        player opp <- player[1];
        ask p { do setup_lists(); }
        environment_cell here <- environment_cell(p.location);

        broken_windows_sensitivity <- 2.0; // celowo mocne, by wymusić erozję do 0
        ask here { disorder <- 1.0; }

        float s <- p.effective_anchor_strength(opp);
        assert s = 0.0; // erosion = 1 - 2.0*1.0 = -1 -> max(0, ...) = 0 -> wynik 0
    }
}

experiment test_pending_action_sync type: test {
    test "pending_action zgadza się z faktycznie zagranym ruchem mimo override kotwicy" {
        anchor_decay_rate <- 0.0;
        broken_windows_sensitivity <- 0.0;
        create player(character: "QLEARN", base_character: "ALLD", character_strength: 1.0, epsilon: 0.0) number: 2;
        player p <- player[0];
        player opp <- player[1];
        ask p { do setup_lists(); }

        string played <- p.QLEARN(opp);
        assert played = "D";
        assert p.pending_action[opp] = played;
    }
}

experiment test_pending_action_sync_broken_windows type: test {
    test "pending_action zgadza się z ruchem po override rozbitej szyby" {
        create player(character: "QLEARN", character_strength: 0.0, epsilon: 0.0, initial_cooperation_bias: 1.0) number: 2;
        player p <- player[0];
        player opp <- player[1];
        ask p { do setup_lists(); }
        environment_cell here <- environment_cell(p.location);

        broken_windows_sensitivity <- 1.0;
        ask here { disorder <- 1.0; }

        bool found_mismatch <- false;
        loop times: 200 {
            string played <- p.strategy(opp);
            if p.pending_action[opp] != played {
                found_mismatch <- true;
                break;
            }
        }
        assert not found_mismatch;
    }
}

experiment test_anchor_not_applied_to_classic type: test {
    test "character_strength pozostaje 0.0 dla agentów klasycznych mimo globalnego parametru" {
        character_strength_qlearn <- 0.9;
        create player(character: "TFT") number: 1 returns: classic;
        create player(character: "QLEARN") number: 1 returns: learners;
        // ta sama akcja, którą wywołuje global.init
        ask classic { do apply_character_params(); }
        ask learners { do apply_character_params(); }
        assert first(classic).character_strength = 0.0;
        assert first(learners).character_strength = 0.9; // kontrola: parametr faktycznie trafia do QLEARN
    }
}

experiment test_disorder_persists_not_just_noise type: test {
    test "powtarzana defekcja w jednym miejscu utrzymuje disorder powyżej poziomu bazowego" {
        environment_cell hot <- environment_cell(0);
        environment_cell cold <- environment_cell(49); // odległa komórka, bez żadnej defekcji
        ask hot { disorder <- 0.0; }
        ask cold { disorder <- 0.0; }

        // symuluj 20 cykli: co 5 cykli nowa defekcja w "hot", nic w "cold"
        loop times: 20 {
            ask hot { disorder <- disorder + disorder_bump_dd; }
            ask hot { do apply_decay(); }
            ask cold { do apply_decay(); }
        }

        assert hot.disorder > cold.disorder;
        assert hot.disorder > 0.3; // nie zdążyło zaniknąć do szumu bliskiego zeru
    }
}

experiment test_reputation_creates_self_fulfilling_bias type: test {
    test "RISKY zmienia zachowanie mimo dobrej historii z akurat tym przeciwnikiem" {
        generalization_threshold <- 3;
        broken_windows_sensitivity <- 0.0;
        create player(character: "QLEARN", epsilon: 0.0, character_strength: 0.0, env_influence: 0.0) number: 2;
        player p <- player[0];
        player opp <- player[1];
        ask p { do setup_lists(); }
        environment_cell here <- environment_cell(p.location);

        loop times: 10 {
            p.lists_per_other[opp] <+ "C";
            p.my_moves_per_other[opp] <+ "C";
        }

        // z tym przeciwnikiem w stanie C|C opłaca się kooperować,
        // ale w "ryzykownym" miejscu agent nauczył się (na innych) defektować
        ask p {
            q_c_per_other[opp]["C|C|SAFE"] <- 5.0;
            q_d_per_other[opp]["C|C|SAFE"] <- 1.0;
            q_c_per_other[opp]["C|C|RISKY"] <- 0.0;
            q_d_per_other[opp]["C|C|RISKY"] <- 3.0;
        }

        assert p.get_state(opp) = "C|C|SAFE";
        assert p.QLEARN(opp) = "C";

        ask p { do register_betrayal(here); }
        ask p { do register_betrayal(here); }
        ask p { do register_betrayal(here); }

        assert p.get_state(opp) = "C|C|RISKY";
        assert p.QLEARN(opp) = "D"; // ta sama historia z opp, inna decyzja - przez reputację miejsca
    }
}

experiment test_new_state_uses_cooperation_bias type: test {
    test "stan odkryty w update_q dostaje prior initial_cooperation_bias, a nie 0/0" {
        broken_windows_sensitivity <- 0.0;
        create player(character: "QLEARN", epsilon: 0.0, character_strength: 0.0, initial_cooperation_bias: 0.8) number: 2;
        player p <- player[0];
        player opp <- player[1];
        ask p { do setup_lists(); }

        string played <- p.QLEARN(opp); // stan START
        p.lists_per_other[opp] <+ "C";
        p.my_moves_per_other[opp] <+ played;
        ask p { do update_q(opp, payoff_R); }

        string next_s <- p.get_state(opp);
        assert abs(p.q_c_per_other[opp][next_s] - 0.8) < 0.001;
        assert abs(p.q_d_per_other[opp][next_s] - 0.2) < 0.001;
    }

    test "remis Q_D = Q_C rozstrzygany losowo, a nie zawsze na D" {
        broken_windows_sensitivity <- 0.0;
        create player(character: "QLEARN", epsilon: 0.0, character_strength: 0.0, initial_cooperation_bias: 0.5) number: 2 returns: pair;
        player p <- pair[0];
        player opp <- pair[1];
        ask p { do setup_lists(); }

        int c_count <- 0;
        loop times: 1000 { if p.QLEARN(opp) = "C" { c_count <- c_count + 1; } }
        assert c_count > 400 and c_count < 600;
    }
}

experiment test_anchor_shifts_early_behavior type: test {
    test "silna kotwica ALLC zwiększa kooperację względem braku kotwicy, przy identycznym Q-learningu w tle" {
        anchor_decay_rate <- 0.15;
        broken_windows_sensitivity <- 0.0;

        create player(character: "QLEARN", base_character: "ALLC", character_strength: 0.9,
                       epsilon: 0.0, initial_cooperation_bias: 0.1) number: 1 returns: with_anchor;
        create player(character: "QLEARN", base_character: "ALLC", character_strength: 0.0,
                       epsilon: 0.0, initial_cooperation_bias: 0.1) number: 1 returns: without_anchor;
        create player number: 1 returns: opps;

        player pa <- first(with_anchor);
        player pb <- first(without_anchor);
        player opp <- first(opps);
        ask pa { do setup_lists(); }
        ask pb { do setup_lists(); }

        int c_count_a <- 0;
        int c_count_b <- 0;
        loop times: 100 {
            if pa.QLEARN(opp) = "C" { c_count_a <- c_count_a + 1; }
            if pb.QLEARN(opp) = "C" { c_count_b <- c_count_b + 1; }
        }

        assert c_count_a > c_count_b;
    }
}
