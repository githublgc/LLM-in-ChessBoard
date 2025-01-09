import os
import re
from typing import List, Dict
import numpy as np
from openai import OpenAI
import collections

client = OpenAI(api_key="your key", base_url="https://api.deepseek.com")

class LLMInterface:
    def __init__(self, model_name: str = "deepseek-chat"):
        self.model_name = model_name
    
    def get_advice(self, prompt: str) -> str:
        response = client.chat.completions.create(
            model=self.model_name,
            messages=[
                {"role": "system", "content": "你是一名擅长五子棋（Gomoku）游戏的专业玩家，现在希望你能根据历史棋局总结一些下棋的关键位置."},
                {"role": "user", "content": prompt},
                {"role": "assistant", "content": ""}
            ],
            stream=False
        )
        return response.choices[0].message.content.strip()

class GomokuReflexion:
    def __init__(self, board_size: int = 15):
        self.board_size = board_size
        self.llm_interface = LLMInterface()
    
    def parse_game(self, lines: List[str]) -> Dict[str, any]:
        game = []
        i = 0
        while i < len(lines):
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
                return {'game': game, 'winner': winner}
        return {'game': game, 'winner': None}
    
    def read_game_file(self, filepath: str) -> Dict[str, any]:
        with open(filepath, 'r') as file:
            lines = [line.strip() for line in file if line.strip()]
            return self.parse_game(lines)
    
    def generate_win_experience_prompt(self, game_data: Dict[str, any], filename: str) -> str:
        game = game_data['game']
        winner = game_data['winner']
        
        prompt = (
            f"以下是文件 {filename} 中的一局五子棋比赛的棋谱数据：\n\n"
            "五子棋是一款在15x15的棋盘上进行的棋类游戏，玩家轮流下子，目标是连成五个相同的棋子。\n"
        )
        
        for move_info in game:
            prompt += (
                f"玩家 {move_info['player']} 下在位置 {move_info['move']}，棋盘状态如下：\n"
                f"{np.array(move_info['state'])}\n\n"
            )
        
        prompt += (
            f"该局游戏的赢家是玩家 {winner}。在真实的五子棋对战中，各种形式多个3个或4个棋子组合相连的情形通常被认为是某种取胜的方法；另外对手经常会因为没看到对角线上的3个或4个棋子相连的失误而输掉比赛。\n"
            f"请结合上述五子棋实战中的领域知识，分析该局游戏中的每一步，最终给出你认为在开局阶段（双方的前5步，即前10个回合内，每有一个玩家走出一步棋子就是一个回合，例如双方各自下一步棋，那么就是2个回合）和中间到最后一方获胜阶段（双方的第6步到最后，也就是第11回合到最终获胜回合）分别给出最关键的三步下棋位置，并分析和指出这些位置是如何导致了赢家获胜，或是失败方是如何失误导致的最终失败。"
        )
        
        return prompt
    
    def save_analysis(self, filename: str, analysis: str):
        with open('analysis.txt', 'a') as file:
            file.write(f"文件 {filename} 的关键位置分析:\n")
            file.write(analysis)
            file.write("\n\n")
    

if __name__ == "__main__":
    analyzer = GomokuReflexion()
    directory = 'test'
    
    # Clear analysis.txt before starting
    with open('analysis.txt', 'w') as file:
        pass
    
    analysis_results = []
    for filename in os.listdir(directory):
        if filename.endswith(".txt"):
            filepath = os.path.join(directory, filename)
            game_data = analyzer.read_game_file(filepath)
            if game_data['winner'] is not None:
                prompt = analyzer.generate_win_experience_prompt(game_data, filename)
                advice = analyzer.llm_interface.get_advice(prompt)
                analyzer.save_analysis(filename, advice)
                analysis_results.append(advice)
            else:
                print(f"文件 {filename} 解析错误，缺少赢家信息。")
    