// SPDX-License-Identifier: GPL-3.0
pragma solidity ^0.8.4;

contract DApp {

    struct Voter{
        uint256 ID; // This is the voter id.
        string expertise_area; // This is the voter's field of expertise.
        mapping(string => uint256) reputation; // Since floats are not allowed, lets store 100 times rep value in it. We can always divide it by 100 in the final step.
        uint256 stake; // This is the stake of voter to prevent sybil attacks.
        bool isregistered; // Specifies if the voter is registered 
        mapping(string => uint256) correct; // Number of correct answers given by the voter.
        mapping(string => uint256) incorrect; // Number of Incorrect answers by the voter.
    }

    struct Vote{
        uint256 V_ID; // ID of the voter.
        uint256 A_ID; // ID of the news article.
        uint256 stake; // Stake that needs to be deposited for a person to vote;
        uint256 vote; // Vote casted which is either 0 or 1.
    }

    struct NewsItem{
        uint256 ID; // Article id. ID = hash(content);
        string content; // Contains the content of the article.
        string area; // Field of expertise the content of this article falls into.
        Vote[] votes; // Votes array which contains votes cast for this article.
        mapping (uint256 => uint256) Voted; // Map between voter id and if he voted or not. 0 if not voted for the article, and 1 if voted for this article. 
        uint256 isValid; // If this article is valid or not. 0 for invalid. 1 for valid 
    }

    uint256 voterid = 0;

    mapping(address => Voter) public voters_list;
    mapping(uint256 => Voter) public id2voter;
    mapping(uint256 => NewsItem) public id2News; 

    event VoterRegistered(address Voter, uint256 id);
    event Votecast(uint256 newsId, uint256 VID); // We can see that our vote is not being broadcast.
    event ReputationUpdate(uint256 id, uint256 reputation, string area);
    event EvaluationDone(uint256 articleid, uint256 truthfulness);
    event StakeUpdate(uint256 id, uint256 stake);
    event CallForVoting(NewsItem article, uint256 fee);
    event VotingConcluded(uint256 newsId, uint256 votecount);

    function reg_fact_checker(string area, uint256 _stake) public{
        address voter = msg.sender;
        require(voters_list[voter].isregistered == false); // Already registered voters cannot register again.
        Voter memory newVoter = Voter({      // memory: This is used for temporary variables. They are erased between (external) function calls and are cheaper to use than storage variables.
            ID: voterid,
            reputation: 100, // Vector full of 100s for all of areas.
            expertise_area: area,
            stake: _stake,
            isregistered: true.
            correct: 0, // Vector full of 0s for all of areas.
            incorrect : 0 // Vector full of 0s for all of areas.
        });
        voters_list[voter] = newVoter;
        id2voter[voterid] = newVoter;
        emit VoterRegistered(voter, voterid);
        voterid++;
    }

    function verify(string content, string area, uint256 fee) public returns(uint256){
        mapping(uint256 => uint256) voted;
        Vote[] votes;
        NewsItem memory newarticle = NewsItem({
            ID: hash(content), // hash of the content of our article.
            content: content,
            area: area,
            votes: votes, // empty array of Vote data structures.
            Voted: voted, // Empty mapping of those who voted.
            isValid: None // Initialized to None.
        })
        emit CallForVoting(newarticle, fee);
        // Watches for event Votecast.
        // deciding number of votes required from some stratergy (say by timelimit 10 minutes)
        emit VotingConcluded(article.ID, article.votes.length);
        evaluate_voting(article,fee);
        return article.isValid;
    }


    function UpdateReputationandStake(NewsItem article, uint256 truth, uint256 fee) private{
        uint256 correct_voters = 0;
        for(uint256 i =0; i < article.votes.length; i++){
            Voter storage voter = id2voter[article.votes[i].V_ID]; // get a reference to the Voter by using storage.
            uint256 a = voter.correct[article.area];
            uint256 b = voter.incorrect[article.area];
            if (article.votes[i].vote == truth) {
                correct_voters += 1;
                voter.correct[article.area] += 1;
                a = voter.correct[article.area];
            }
            else{
                voter.incorrect += 1;
                b = voter.incorrect[article.area];
                fee += article.votes[i].stake/10; // ?? Using 10% as punishment, can change later.
                voter.stake = (vote.stake*9)/10; // Modify the stake of incorrect voters.
                emit StakeUpdate(article.votes[i].V_ID,id2voter[article.votes[i].V_ID].stake);  
            }
            voter.reputation[article.area] = (uint256(a))/(uint256(a) + uint256(b));
            emit ReputationUpdate(article.votes[i].V_ID,voter.reputation[area], area);
        }
        for(uint256 i = 0; i < article.votes.length; i++){
            Voter storage voter = id2voter[article.votes[i].V_ID]; // get a reference to the Voter by using storage
            if(article.votes[i].vote == truth){
                voter.stake += fee/correct_voters; // Incentivizing the rational miners. Here we can also distribute this total fee by their weights.
                emit StakeUpdate(article.votes[i].V_ID,voter.stake);
            }
        }
    }

    function vote(uint256 newsId, uint256 VID, uint256 vote) private{
        NewsItem storage article = id2News[newsId];
        require(id2voter[VID].isregistered == true); // Only registered voters can vote.
        require(article.Voted[VID] == 0); // A previously voted user cannot vote again.
        uint256 stake = id2voter[VID].stake;
        Vote memory v = Vote(VID,newsId,stake,vote); // ?? make sure a voter can vote only once for an article.
        require(vote == 0 || vote == 1); // Making sure vote is either 0 or 1.
        article.Voted[VID] = 1; // Marking that voter has voted.
        article.votes.push(v);
        emit Votecast(newsId,VID); // Not revealing our votes to general public.
    }

    function evaluate_voting(NewsItem Article, uint256 fee) private{
        NewsItem storage article = id2News[Article.ID]; // get a reference to the NewsItem in the mapping
        string area = article.area;
        uint256 weighted_sum = 0;
        uint256 total = 0;
        for(uint256 i =0; i < article.votes.length; i++){
            weighted_sum += article.votes[i].vote*id2voter[article.votes[i].V_ID].reputation[area]*sqrt(id2voter[article.votes[i].V_ID].stake); // weight += vote*reputation*sqrt(stake), and assume sqrt function is already somewhere defined.
            total += id2voter[article.votes[i].V_ID].reputation[area]*sqrt(id2voter[article.votes[i].V_ID].stake);
        }
        uint256 final_result = weighted_sum * 100/total;
        if(final_result > 50){
            article.isValid = 1;
        }
        else{
            article.isValid = 0;
        }
        UpdateReputationandStake(article, article.isValid,fee);
        emit EvaluationDone(article.ID, article.isValid);
    }

    function harsh_evaluate() {
        // Same as the evaluate_voting function. but we will punish higher by increasing 
        // correct and incorrect by some higher values (say 10 instead of a 1) and we will also 
        // punish by taking higher percent of stake from incorrect voters. 
    }

    function selectcommittee() {
        // The committee will be selected based on the reputation score and the number of votes
        // cast. Reputation alone would not be enough to get selected to the committee.  
        // Committee members upload an article of whose truth value they already know
        // and test the remaining voter, who are unaware of it and use harsh_evaluate() with
        // this function.
    }


}