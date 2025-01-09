import os
import re
from typing import List, Dict
import numpy as np
from openai import OpenAI

client = OpenAI(api_key="your key", base_url="https://api.deepseek.com")

class LLMInterface:
    def __init__(self, model_name: str = "deepseek-chat"):
        self.model_name = model_name
    
    def get_advice(self, prompt: str) -> str:
        response = client.chat.completions.create(
            model=self.model_name,
            messages=[
                {"role": "system", "content": "You are an expert in Gomoku strategy analysis. Summarize the winning strategies based on the provided game data."},
                {"role": "user", "content": prompt},
            ],
            stream=False
        )
        return response.choices[0].message.content.strip()

class GomokuReflexion:
    def __init__(self, board_size: int = 15):
        self.board_size = board_size
        self.llm_interface = LLMInterface()
    
    def parse_games(self, lines: List[str]) -> List[Dict[str, any]]:
        games = []
        i = 0
        while i < len(lines):
            if lines[i].startswith("game:"):
                game_num = int(lines[i].split(":")[1].strip())
                i += 1
                game = []
                while i < len(lines) and not lines[i].startswith("game:"):
                    if lines[i].startswith("player:"):
                        player = int(lines[i].split(":")[1].strip())
                        i += 1
                        if lines[i].startswith("x,y:"):
                            move_str = lines[i].split(":")[1].strip()
                            x, y = map(int, move_str.strip("()").split(","))
                            move = (x, y)
                            i += 1
                            if lines[i].startswith("state:"):
                                i += 1
                                state = []
                                for _ in range(self.board_size):
                                    state_line = list(map(int, lines[i].strip().strip("[]").split(",")))
                                    state.append(state_line)
                                    i += 1
                                game.append({'player': player, 'move': move, 'state': state})
                        else:
                            i += 1
                    elif lines[i].startswith("winner:"):
                        winner = int(lines[i].split(":")[1].strip())
                        i += 1
                        games.append({'game': game, 'winner': winner})
                        break
            else:
                i += 1
        return games
    
    def read_game_file(self, filepath: str) -> List[Dict[str, any]]:
        with open(filepath, 'r') as file:
            lines = [line.strip() for line in file if line.strip()]
            return self.parse_games(lines)
    
    def generate_win_experience_prompt(self, game_data: Dict[str, any], phase: str) -> str:
        game = game_data['game']
        winner = game_data['winner']
        
        prompt = (
            f"以下是{phase}阶段的某一局五子棋比赛棋谱数据中筛选过后几个导致最终胜利或失败重要的下棋步骤，赢家是玩家 {winner}。请总结在此阶段的获胜策略，同时你也可以观察棋盘状态和对手下棋的过程，反思对手的下棋策略是因为什么导致了失败，从而进一步总结对手可能出现的错误并利用这些错误总结获胜经验。\n\n"
        )
        
        for move_info in game:
            prompt += (
                f"玩家 {move_info['player']} 下在位置 {move_info['move']}，棋盘状态如下：\n"
                f"{np.array(move_info['state'])}\n\n"
            )
        
        return prompt
    
    def save_reflexion(self, phase: str, strategy: str):
        with open('reflexion.txt', 'a', encoding='utf-8') as file:
            file.write(f"{phase}获胜策略:\n")
            file.write(strategy)
            file.write("\n\n")

if __name__ == "__main__":
    analyzer = GomokuReflexion()
    
    # Clear reflexion.txt before starting
    with open('reflexion.txt', 'w', encoding='utf-8') as file:
        pass
    
    # Read phase1.txt (opening phase)
    filepath1 = 'phase1.txt'
    games1 = analyzer.read_game_file(filepath1)
    opening_strategies = []
    for game_data in games1:
        if game_data['winner'] is not None:
            prompt1 = analyzer.generate_win_experience_prompt(game_data, "开局")
            advice1 = analyzer.llm_interface.get_advice(prompt1)
            opening_strategies.append(advice1)
        else:
            print("phase1.txt 中某局解析错误，缺少赢家信息。")
    # Aggregate opening strategies
    opening_summary = "\n".join(opening_strategies)
    analyzer.save_reflexion("开局", opening_summary)
    
    # Read phase2.txt (middle to end game phase)
    filepath2 = 'phase2.txt'
    games2 = analyzer.read_game_file(filepath2)
    middle_end_strategies = []
    for game_data in games2:
        if game_data['winner'] is not None:
            prompt2 = analyzer.generate_win_experience_prompt(game_data, "中局到终局")
            advice2 = analyzer.llm_interface.get_advice(prompt2)
            middle_end_strategies.append(advice2)
        else:
            print("phase2.txt 中某局解析错误，缺少赢家信息。")
    # Aggregate middle to end game strategies
    middle_end_summary = "\n".join(middle_end_strategies)
    analyzer.save_reflexion("中局到终局", middle_end_summary)