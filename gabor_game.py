import tkinter as tk
from tkinter import messagebox
import numpy as np
from PIL import Image, ImageTk
import random

# ==========================================
# 1. 핵심 엔진: 가보르 패치 이미지 생성 함수
# ==========================================
def create_gabor_patch(size, theta, frequency, sigma, contrast):
    """
    가보르 패치 이미지를 생성하여 PIL Image 객체로 반환합니다.
    """
    x, y = np.meshgrid(np.linspace(-1, 1, size), np.linspace(-1, 1, size))
    
    x_theta = x * np.cos(theta) + y * np.sin(theta)
    y_theta = -x * np.sin(theta) + y * np.cos(theta)
    
    grating = np.cos(2 * np.pi * frequency * x_theta)
    envelope = np.exp(-(x_theta**2 + y_theta**2) / (2 * sigma**2))
    gabor = grating * envelope * contrast
    
    img_array = np.uint8((gabor + 1) / 2 * 255)
    return Image.fromarray(img_array, 'L')

# ==========================================
# 2. 메인 앱 컨트롤러
# ==========================================
class GaborGameApp:
    def __init__(self, root):
        self.root = root
        self.root.title("눈 운동 가보르 게임")
        self.root.geometry("600x800")
        self.root.configure(bg='#333333')
        
        # 현재 활성화된 프레임을 저장
        self.current_frame = None
        
        # 초기 화면: 메인 메뉴 표시
        self.show_main_menu()

    def clear_frame(self):
        if self.current_frame:
            self.current_frame.destroy()
        self.current_frame = None

    def show_main_menu(self):
        self.clear_frame()
        self.current_frame = MainMenu(self.root, self)
        self.current_frame.pack(fill="both", expand=True)

    def start_target_match(self):
        self.clear_frame()
        self.current_frame = TargetMatchGame(self.root, self)
        self.current_frame.pack(fill="both", expand=True)

    def start_pair_match(self):
        self.clear_frame()
        self.current_frame = PairMatchGame(self.root, self)
        self.current_frame.pack(fill="both", expand=True)

# ==========================================
# 3. UI 클래스들이 상속할 기본 프레임
# ==========================================
class GameFrame(tk.Frame):
    def __init__(self, master, controller, **kwargs):
        super().__init__(master, **kwargs)
        self.controller = controller
        self.configure(bg='#333333')

# ==========================================
# 4. 메인 메뉴
# ==========================================
class MainMenu(GameFrame):
    def __init__(self, master, controller):
        super().__init__(master, controller)
        
        tk.Label(self, text="눈 운동 가보르 게임", font=("Arial", 24, "bold"), bg='#333333', fg='white').pack(pady=50)
        
        tk.Label(self, text="게임 방식을 선택하세요", font=("Arial", 14), bg='#333333', fg='#AAAAAA').pack(pady=20)
        
        btn_target = tk.Button(self, text="1. 동일한 무늬 찾기 (기본)", font=("Arial", 14), width=25, height=2,
                               command=controller.start_target_match)
        btn_target.pack(pady=10)
        
        btn_pair = tk.Button(self, text="2. 짝 맞추기 (심화)", font=("Arial", 14), width=25, height=2,
                             command=controller.start_pair_match)
        btn_pair.pack(pady=10)

        tk.Label(self, text="매일 꾸준히 하면 시력 개선에 도움이 됩니다.", font=("Arial", 10), bg='#333333', fg='#666666').pack(side="bottom", pady=30)

# ==========================================
# 5. 게임 모드 1: 동일한 무늬 찾기 (기존)
# ==========================================
class TargetMatchGame(GameFrame):
    def __init__(self, master, controller):
        super().__init__(master, controller)
        
        self.score = 0
        self.round = 1
        self.target_theta = 0
        self.image_refs = []

        # 상단 네비게이션
        nav_frame = tk.Frame(self, bg='#333333')
        nav_frame.pack(fill="x", padx=10, pady=10)
        tk.Button(nav_frame, text="< 메뉴로", command=controller.show_main_menu, bg='gray').pack(side="left")
        
        # 정보창
        self.info_label = tk.Label(self, text=f"Score: {self.score} | Round: {self.round}", font=("Arial", 16), bg='#333333', fg='white')
        self.info_label.pack(pady=5)

        # 타겟 영역
        tk.Label(self, text="▼ 이 무늬와 같은 것을 찾으세요 ▼", font=("Arial", 12), bg='#333333', fg='#AAAAAA').pack()
        self.target_canvas = tk.Canvas(self, width=150, height=150, bg='#333333', highlightthickness=0)
        self.target_canvas.pack(pady=10)

        # 피드백
        self.feedback_label = tk.Label(self, text="", font=("Arial", 14, "bold"), bg='#333333', fg='yellow')
        self.feedback_label.pack(pady=5)

        # 그리드
        self.grid_frame = tk.Frame(self, bg='#333333')
        self.grid_frame.pack(pady=10)
        self.grid_buttons = []
        for i in range(3):
            row_buttons = []
            for j in range(3):
                btn = tk.Button(self.grid_frame, bg='gray', borderwidth=2, relief="ridge")
                btn.grid(row=i, column=j, padx=10, pady=10)
                row_buttons.append(btn)
            self.grid_buttons.append(row_buttons)

        self.start_new_round()

    def start_new_round(self):
        self.image_refs = []
        self.feedback_label.config(text="")
        self.info_label.config(text=f"Score: {self.score} | Round: {self.round}")

        patch_size = 120
        frequency = 4.0 + (self.round * 0.2)
        sigma = 0.35
        contrast = 0.9

        self.target_theta = np.radians(random.choice([0, 30, 45, 60, 90, 120, 135, 150]))
        
        target_img = ImageTk.PhotoImage(create_gabor_patch(patch_size, self.target_theta, frequency, sigma, contrast))
        self.target_canvas.create_image(75, 75, image=target_img)
        self.image_refs.append(target_img)

        grid_thetas = [self.target_theta]
        while len(grid_thetas) < 9:
            diff = np.radians(random.randint(20, 160)) 
            distractor_theta = (self.target_theta + diff) % np.radians(180)
            grid_thetas.append(distractor_theta)
        
        random.shuffle(grid_thetas)

        idx = 0
        for i in range(3):
            for j in range(3):
                theta = grid_thetas[idx]
                img_tk = ImageTk.PhotoImage(create_gabor_patch(patch_size, theta, frequency, sigma, contrast))
                self.image_refs.append(img_tk)
                
                btn = self.grid_buttons[i][j]
                # 기존 command 제거하고 bind 사용. highlightthickness=0 초기화
                btn.config(image=img_tk, state="normal", bg="gray", relief="ridge", highlightthickness=0)
                # 기존 바인딩이 쌓이지 않게 unbind 시도하거나 그냥 덮어씌움 (새 라운드마다 위젯 재사용하므로)
                # bind는 add=+가 없으면 덮어씀.
                btn.bind('<Button-1>', lambda e, t=theta, r=i, c=j: self.check_answer(t, r, c))
                
                idx += 1

    def check_answer(self, selected_theta, row, col):
        # 버튼 상태가 disabled면 무시 (bind는 state=disabled여도 이벤트 발생할 수 있음)
        btn = self.grid_buttons[row][col]
        if btn['state'] == 'disabled':
            return

        if np.isclose(selected_theta, self.target_theta):
            # 정답: 초록색 테두리
            btn.config(highlightbackground='#55FF55', highlightthickness=4, highlightcolor='#55FF55')
            self.score += 10
            self.round += 1
            self.feedback_label.config(text="정답입니다!", fg='#55FF55')
            self.disable_buttons()
            self.after(1000, self.start_new_round)
        else:
            # 오답: 빨간색 테두리
            btn.config(highlightbackground='#FF5555', highlightthickness=4, highlightcolor='#FF5555')
            self.feedback_label.config(text="다시 집중해서 찾아보세요.", fg='#FF5555')
            
    def disable_buttons(self):
        for row in self.grid_buttons:
            for btn in row:
                btn.config(state="disabled")

# ==========================================
# 6. 게임 모드 2: 짝 맞추기 (신규)
# ==========================================
class PairMatchGame(GameFrame):
    def __init__(self, master, controller):
        super().__init__(master, controller)
        
        self.score = 0
        self.round = 1
        self.image_refs = []
        self.selected_buttons = [] # (button, theta, index)
        self.matched_indices = set()
        
        # 상단 네비게이션
        nav_frame = tk.Frame(self, bg='#333333')
        nav_frame.pack(fill="x", padx=10, pady=10)
        tk.Button(nav_frame, text="< 메뉴로", command=controller.show_main_menu, bg='gray').pack(side="left")

        # 정보창
        self.info_label = tk.Label(self, text=f"Round: {self.round}", font=("Arial", 16), bg='#333333', fg='white')
        self.info_label.pack(pady=5)
        
        tk.Label(self, text="같은 무늬 짝을 모두 찾으세요", font=("Arial", 12), bg='#333333', fg='#AAAAAA').pack()

        # 피드백
        self.feedback_label = tk.Label(self, text="", font=("Arial", 14, "bold"), bg='#333333', fg='yellow')
        self.feedback_label.pack(pady=5)

        # 그리드 컨테이너 (동적으로 버튼 생성 예정)
        self.grid_frame = tk.Frame(self, bg='#333333')
        self.grid_frame.pack(pady=20)
        
        self.start_new_round()

    def start_new_round(self):
        # 변수 초기화
        for widget in self.grid_frame.winfo_children():
            widget.destroy()
        
        self.image_refs = []
        self.selected_buttons = []
        self.matched_indices = set()
        self.feedback_label.config(text="")
        self.info_label.config(text=f"Round: {self.round}")

        # 난이도 설정 (쌍의 개수 증가)
        num_pairs = min(2 + (self.round - 1) * 2, 8)
        num_items = num_pairs * 2
        
        # 그리드 사이즈 결정
        if num_items <= 4:
            rows, cols = 2, 2
        elif num_items <= 8:
            rows, cols = 4, 2 # or 2, 4
        elif num_items <= 12:
            rows, cols = 4, 3
        else:
            rows, cols = 4, 4
            
        # 쌍 생성
        base_thetas = []
        for _ in range(num_pairs):
            theta = np.radians(random.randint(0, 179))
            base_thetas.append(theta)
            
        game_thetas = base_thetas * 2 # 2개씩 복제
        random.shuffle(game_thetas)
        
        patch_size = 100
        frequency = 4.0
        sigma = 0.35
        contrast = 0.9

        self.buttons = []
        
        for r in range(rows):
            for c in range(cols):
                idx = r * cols + c
                if idx >= len(game_thetas): break
                
                theta = game_thetas[idx]
                img_tk = ImageTk.PhotoImage(create_gabor_patch(patch_size, theta, frequency, sigma, contrast))
                self.image_refs.append(img_tk)
                
                # Mac에서 테두리 색을 표현하기 위해 highlightbackground 사용
                btn = tk.Button(self.grid_frame, image=img_tk, bg='gray', borderwidth=2, relief="ridge", 
                                highlightthickness=0)
                # command 대신 bind 사용
                btn.bind('<Button-1>', lambda e, b=btn, t=theta, i=idx: self.on_card_click(b, t, i))
                
                btn.grid(row=r, column=c, padx=5, pady=5)
                self.buttons.append(btn)

    def on_card_click(self, btn, theta, index):
        if btn['state'] == 'disabled':
            return
            
        if index in self.matched_indices:
            return
        if any(s[2] == index for s in self.selected_buttons):
            # 이미 선택된거 다시 누르면 취소 기능 (선택적)
            return
        if len(self.selected_buttons) >= 2:
            return

        # 선택효과: 노란색 테두리
        btn.config(highlightbackground='#FFFF00', highlightthickness=4, highlightcolor='#FFFF00')
        self.selected_buttons.append((btn, theta, index))

        if len(self.selected_buttons) == 2:
            self.master.after(500, self.check_pair)

    def check_pair(self):
        btn1, theta1, idx1 = self.selected_buttons[0]
        btn2, theta2, idx2 = self.selected_buttons[1]

        if np.isclose(theta1, theta2): # 매치 성공
            self.feedback_label.config(text="매치 성공!", fg='#55FF55')
            
            btn1.config(bg='#333333', state="disabled", relief="flat", highlightthickness=0, image='') 
            btn2.config(bg='#333333', state="disabled", relief="flat", highlightthickness=0, image='')
            self.matched_indices.add(idx1)
            self.matched_indices.add(idx2)
            
            if len(self.matched_indices) == len(self.image_refs):
                self.feedback_label.config(text="모든 짝을 찾았습니다!", fg='#55FF55')
                self.round += 1
                self.after(1000, self.start_new_round)
        else: # 매치 실패
            self.feedback_label.config(text="다릅니다.", fg='#FF5555')
            # 다시 원래대로 (회색 혹은 테두리 없음)
            btn1.config(highlightthickness=0, bg='gray')
            btn2.config(highlightthickness=0, bg='gray')
        
        self.selected_buttons = []

if __name__ == "__main__":
    root = tk.Tk()
    app = GaborGameApp(root)
    root.mainloop()

