#!/user/bin/env python
# -*- coding:utf-8 -*-
# 作者：周桂华
# 开发时间: 2021/7/10 20:37

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as Ec
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.action_chains import ActionChains
import time
import os
import random
import cv2
import numpy as np
import undetected_chromedriver.v2 as uc
import requests

# 知乎账号
USERNAME = "*****"
# 密码
PASSWD = "*****"


class Code(object):

    def __init__(self, slider_ele=None, background_ele=None, count=1, save_image=False):
        self.count = count
        self.save_images = save_image
        self.slider_ele = slider_ele
        self.background_ele = background_ele

    def get_slide_locus(self, distance):
        distance += 8
        v = 0
        m = 0.3
        tracks = []
        current = 0
        mid = distance * 4 / 5
        while current <= distance:
            if current < mid:
                a = 2
            else:
                a = -3
            v0 = v
            s = v0 * m + 0.5 * a * (m ** 2)
            current += s
            tracks.append(round(s))
            v = v0 + a * m
        return tracks

    def slide_verification(self, driver, slide_element, distance):
        print('滑动距离是: ', distance)
        # 根据滑动的距离生成滑动轨迹
        locus = self.get_slide_locus(distance)
        print('生成的滑动轨迹为:{},轨迹的距离之和为{}'.format(locus, distance))
        # 按下鼠标左键
        ActionChains(driver).click_and_hold(slide_element).perform()
        time.sleep(0.5)
        # 遍历轨迹进行滑动
        for loc in locus:
            time.sleep(0.01)
            # 修改scrapy的源码 selenium\webdriver\common\actions\pointer_input.py中将DEFAULT_MOVE_DURATION改为50，否则滑动很慢
            ActionChains(driver).move_by_offset(loc, random.randint(-5, 5)).perform()
            ActionChains(driver).context_click(slide_element)

        # 释放鼠标
        ActionChains(driver).release(on_element=slide_element).perform()

    def onload_save_img(self, url, filename="image.png"):
        '''
        下载图片并保存
        :param url: 图片网址
        :param filename: 图片名称
        :return:
        '''
        try:
            response = requests.get(url)
        except Exception as e:
            print('图片下载失败')
            raise e
        else:
            with open(filename, 'wb') as f:
                f.write(response.content)

    def get_element_slide_distance(self, slider_ele, background_ele, correct=0):
        # 获取验证码的图片
        slider_url = slider_ele.get_attribute('src')
        background_url = background_ele.get_attribute('src')
        # 下载验证码链接
        slider = 'slider.jpg'
        background = 'background.jpg'
        self.onload_save_img(slider_url, slider)
        self.onload_save_img(background_url, background)
        # 进行色度图片, 转化为numpy 中的数组类型数据
        slider_pic = cv2.imread(slider, 0)
        background_pic = cv2.imread(background, 0)
        # 获取缺口数组的形状
        width, height = slider_pic.shape[::-1]
        # 将处理之后的图片另存
        slider01 = 'slider01.jpg'
        slider02 = 'slider02.jpg'
        background01 = 'background01.jpg'
        cv2.imwrite(slider01, slider_pic)
        cv2.imwrite(background01, background_pic)
        # 读取另存的滑块
        slider_pic = cv2.imread(slider01)
        # 进行色彩转化
        slider_pic = cv2.cvtColor(slider_pic, cv2.COLOR_BGR2GRAY)
        # 获取色差的绝对值
        slider_pic = abs(255 - slider_pic)
        # 保存图片
        cv2.imwrite(slider02, slider_pic)
        # 读取滑块
        slider_pic = cv2.imread(slider02)
        # 读取背景图
        background_pic = cv2.imread(background01)
        time.sleep(3)
        result = cv2.matchTemplate(slider_pic, background_pic, cv2.TM_CCOEFF_NORMED)
        # 通过数组运算，获取图片缺口位置
        top, left = np.unravel_index(result.argmax(), result.shape)
        # 背景图缺口坐标
        print('当前滑块缺口位置', (left, top, left + width, top + height))
        # 判读是否需求保存识别过程中的截图文件
        if self.save_images:
            loc = [(left + correct, top + correct), (left + width - correct, top + height - correct)]
            self.image_crop(background, loc)
        else:
            # 删除临时文件
            os.remove(slider01)
            os.remove(slider02)
            os.remove(background01)
            os.remove(background)
            os.remove(slider)
        # 返回需要移动的位置距离
        return left

    def image_crop(self, image, loc):
        cv2.rectangle(image, loc[0], loc[1], (7, 249, 151), 2)
        cv2.imshow('Show', image)
        cv2.waitKey(0)
        cv2.destroyAllWindows()


class Login(object):
    def __init__(self, user, password, retry):
        # 创建一个参数对象，用来控制chrome以无界面模式打开
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument('--headless')  # # 浏览器不提供可视化页面
        chrome_options.add_argument('--disable-gpu')  # 禁用GPU加速,GPU加速可能会导致Chrome出现黑屏，且CPU占用率高达80%以上
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')

        self.browser = uc.Chrome()
        self.wait = WebDriverWait(self.browser, 20)
        self.url = 'https://www.zhihu.com/signin'
        self.sli = Code()
        self.user = user
        self.password = password
        self.retry = retry  # 重试次数
        self.cookies = ''

    def login(self):
        # 请求网址
        self.browser.get(self.url)
        self.browser.get(self.url)
        login_element = self.browser.find_element_by_xpath(
            '//*[@id="root"]/div/main/div/div/div/div[1]/div/form/div[1]/div[2]')
        self.browser.execute_script("arguments[0].click();", login_element)
        time.sleep(3)

        # 输入账号
        username = self.wait.until(
            Ec.element_to_be_clickable((By.CSS_SELECTOR, '.SignFlow-account input'))
        )
        username.send_keys(self.user)
        # 输入密码
        password = self.wait.until(
            Ec.element_to_be_clickable((By.CSS_SELECTOR, '.SignFlow-password input'))
        )
        password.send_keys(self.password)

        # 登录框
        submit = self.wait.until(
            Ec.element_to_be_clickable((By.CSS_SELECTOR, '.Button.SignFlow-submitButton'))
        )
        submit.click()
        time.sleep(3)

        k = 1
        while k < self.retry:
            # 1. 获取原图
            bg_img = self.wait.until(
                Ec.presence_of_element_located((By.CSS_SELECTOR, '.yidun_bgimg .yidun_bg-img'))
            )

            front_img = self.wait.until(
                Ec.presence_of_element_located((By.CSS_SELECTOR, '.yidun_bgimg .yidun_jigsaw'))
            )
            # 获取验证码滑动距离
            distance = self.sli.get_element_slide_distance(front_img, bg_img)
            print('滑动距离是', distance)

            # 2. 乘缩放比例， -去  滑块前面的距离  下面给介绍
            distance = distance - 4
            print('实际滑动距离是', distance)

            # 滑块对象
            element = self.browser.find_element_by_css_selector(
                '.yidun_slider')
            # 滑动函数
            self.sli.slide_verification(self.browser, element, distance)

            # 滑动之后的url链接
            time.sleep(5)
            # 登录框
            try:
                submit = self.wait.until(
                    Ec.element_to_be_clickable((By.CSS_SELECTOR, '.Button.SignFlow-submitButton'))
                )
                submit.click()
                time.sleep(5)
            except:
                pass
            end_url = self.browser.current_url
            if end_url == "https://www.zhihu.com/":
                return self.get_cookies()
            else:
                time.sleep(3)
                k += 1
        return None

    def get_cookies(self):
        cookies = self.browser.get_cookies()

        for cookie in cookies:
            self.cookies += '{}={};'.format(cookie.get('name'), cookie.get('value'))
        return self.cookies

    def __del__(self):
        self.browser.close()
        print('界面关闭')


if __name__ == "__main__":
    login = Login(USERNAME, PASSWD, 5)
    login.login()

