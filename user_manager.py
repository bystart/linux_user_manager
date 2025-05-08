#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import pwd
import grp
import subprocess
from typing import List, Optional
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt, Confirm
from rich.panel import Panel
from rich import print as rprint

console = Console()

class UserManager:
    def __init__(self):
        self.console = Console()
        self.check_root_privileges()

    def check_root_privileges(self):
        """检查是否具有root权限"""
        if os.geteuid() != 0:
            self.console.print("[red]错误：此程序需要root权限才能运行！[/red]")
            self.console.print("请使用 sudo 运行此程序")
            sys.exit(1)

    def run_command(self, command: List[str]) -> tuple:
        """执行shell命令"""
        try:
            result = subprocess.run(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                check=True
            )
            return True, result.stdout
        except subprocess.CalledProcessError as e:
            return False, e.stderr

    def list_users(self):
        """列出所有用户"""
        table = Table(title="系统用户列表")
        table.add_column("用户名", style="cyan")
        table.add_column("UID", style="green")
        table.add_column("GID", style="yellow")
        table.add_column("主目录", style="blue")
        table.add_column("Shell", style="magenta")

        for user in pwd.getpwall():
            table.add_row(
                user.pw_name,
                str(user.pw_uid),
                str(user.pw_gid),
                user.pw_dir,
                user.pw_shell
            )

        self.console.print(table)

    def create_user(self):
        """创建新用户"""
        try:
            username = Prompt.ask("请输入新用户名")
            
            # 检查用户是否已存在
            try:
                pwd.getpwnam(username)
                self.console.print(f"[red]错误：用户 {username} 已存在！[/red]")
                return
            except KeyError:
                pass

            # 获取用户信息
            home_dir = Prompt.ask("请输入主目录", default=f"/home/{username}")
            shell = Prompt.ask("请输入shell", default="/bin/bash")
            create_home = Confirm.ask("是否创建主目录？", default=True)
            set_password = Confirm.ask("是否设置密码？", default=True)

            # 构建useradd命令
            cmd = ["useradd"]
            if create_home:
                cmd.append("-m")
            cmd.extend(["-d", home_dir, "-s", shell, username])

            success, output = self.run_command(cmd)
            if success:
                self.console.print(f"[green]成功创建用户 {username}[/green]")
                if set_password:
                    self.set_password(username)
            else:
                self.console.print(f"[red]创建用户失败：{output}[/red]")
        except KeyboardInterrupt:
            self.console.print("\n[yellow]已取消创建用户[/yellow]")

    def delete_user(self):
        """删除用户"""
        username = Prompt.ask("请输入要删除的用户名")
        
        # 检查用户是否存在
        try:
            pwd.getpwnam(username)
        except KeyError:
            self.console.print(f"[red]错误：用户 {username} 不存在！[/red]")
            return

        remove_home = Confirm.ask("是否删除用户主目录？", default=True)
        cmd = ["userdel"]
        if remove_home:
            cmd.append("-r")
        cmd.append(username)

        success, output = self.run_command(cmd)
        if success:
            self.console.print(f"[green]成功删除用户 {username}[/green]")
        else:
            self.console.print(f"[red]删除用户失败：{output}[/red]")

    def set_password(self, username: Optional[str] = None):
        """设置用户密码"""
        try:
            if username is None:
                username = Prompt.ask("请输入用户名")

            # 检查用户是否存在
            try:
                pwd.getpwnam(username)
            except KeyError:
                self.console.print(f"[red]错误：用户 {username} 不存在！[/red]")
                return

            # 使用chpasswd命令设置密码
            password = Prompt.ask("请输入新密码", password=True)
            confirm_password = Prompt.ask("请再次输入密码", password=True)

            if password != confirm_password:
                self.console.print("[red]错误：两次输入的密码不一致！[/red]")
                return

            # 使用echo和chpasswd命令设置密码
            cmd = f"echo '{username}:{password}' | chpasswd"
            success, output = self.run_command(["bash", "-c", cmd])
            
            if success:
                self.console.print(f"[green]成功设置用户 {username} 的密码[/green]")
            else:
                self.console.print(f"[red]设置密码失败：{output}[/red]")
        except KeyboardInterrupt:
            self.console.print("\n[yellow]已取消设置密码[/yellow]")

    def modify_user(self):
        """修改用户信息"""
        try:
            username = Prompt.ask("请输入要修改的用户名")
            
            # 检查用户是否存在
            try:
                user_info = pwd.getpwnam(username)
            except KeyError:
                self.console.print(f"[red]错误：用户 {username} 不存在！[/red]")
                return

            self.console.print(Panel(f"当前用户信息：\n"
                                f"用户名：{user_info.pw_name}\n"
                                f"UID：{user_info.pw_uid}\n"
                                f"GID：{user_info.pw_gid}\n"
                                f"主目录：{user_info.pw_dir}\n"
                                f"Shell：{user_info.pw_shell}"))

            new_home = Prompt.ask("请输入新的主目录", default=user_info.pw_dir)
            new_shell = Prompt.ask("请输入新的shell", default=user_info.pw_shell)

            cmd = ["usermod", "-d", new_home, "-s", new_shell, username]
            success, output = self.run_command(cmd)
            if success:
                self.console.print(f"[green]成功修改用户 {username} 的信息[/green]")
            else:
                self.console.print(f"[red]修改用户信息失败：{output}[/red]")
        except KeyboardInterrupt:
            self.console.print("\n[yellow]已取消修改用户信息[/yellow]")

    def list_groups(self):
        """列出所有用户组"""
        table = Table(title="系统用户组列表")
        table.add_column("组名", style="cyan")
        table.add_column("GID", style="green")
        table.add_column("成员", style="yellow")

        for group in grp.getgrall():
            members = ", ".join(group.gr_mem) if group.gr_mem else "无"
            table.add_row(
                group.gr_name,
                str(group.gr_gid),
                members
            )

        self.console.print(table)

    def create_group(self):
        """创建新用户组"""
        groupname = Prompt.ask("请输入新组名")
        
        # 检查组是否已存在
        try:
            grp.getgrnam(groupname)
            self.console.print(f"[red]错误：组 {groupname} 已存在！[/red]")
            return
        except KeyError:
            pass

        cmd = ["groupadd", groupname]
        success, output = self.run_command(cmd)
        if success:
            self.console.print(f"[green]成功创建组 {groupname}[/green]")
        else:
            self.console.print(f"[red]创建组失败：{output}[/red]")

    def delete_group(self):
        """删除用户组"""
        groupname = Prompt.ask("请输入要删除的组名")
        
        # 检查组是否存在
        try:
            grp.getgrnam(groupname)
        except KeyError:
            self.console.print(f"[red]错误：组 {groupname} 不存在！[/red]")
            return

        cmd = ["groupdel", groupname]
        success, output = self.run_command(cmd)
        if success:
            self.console.print(f"[green]成功删除组 {groupname}[/green]")
        else:
            self.console.print(f"[red]删除组失败：{output}[/red]")

    def add_user_to_group(self):
        """将用户添加到组"""
        username = Prompt.ask("请输入用户名")
        groupname = Prompt.ask("请输入组名")

        # 检查用户和组是否存在
        try:
            pwd.getpwnam(username)
        except KeyError:
            self.console.print(f"[red]错误：用户 {username} 不存在！[/red]")
            return

        try:
            grp.getgrnam(groupname)
        except KeyError:
            self.console.print(f"[red]错误：组 {groupname} 不存在！[/red]")
            return

        cmd = ["usermod", "-a", "-G", groupname, username]
        success, output = self.run_command(cmd)
        if success:
            self.console.print(f"[green]成功将用户 {username} 添加到组 {groupname}[/green]")
        else:
            self.console.print(f"[red]添加用户到组失败：{output}[/red]")

def main_menu():
    """显示主菜单"""
    manager = UserManager()
    
    while True:
        try:
            console.clear()
            console.print(Panel.fit(
                "[bold cyan]Linux用户管理[/bold cyan]\n"
                "1. 列出所有用户\n"
                "2. 创建新用户\n"
                "3. 删除用户\n"
                "4. 修改用户信息\n"
                "5. 设置用户密码\n"
                "6. 列出所有用户组\n"
                "7. 创建新用户组\n"
                "8. 删除用户组\n"
                "9. 将用户添加到组\n"
                "0. 退出程序",
                title="主菜单"
            ))

            choice = Prompt.ask("请选择操作", choices=["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"])

            if choice == "0":
                console.print("[yellow]感谢使用，再见！[/yellow]")
                break

            try:
                if choice == "1":
                    manager.list_users()
                elif choice == "2":
                    manager.create_user()
                elif choice == "3":
                    manager.delete_user()
                elif choice == "4":
                    manager.modify_user()
                elif choice == "5":
                    manager.set_password()
                elif choice == "6":
                    manager.list_groups()
                elif choice == "7":
                    manager.create_group()
                elif choice == "8":
                    manager.delete_group()
                elif choice == "9":
                    manager.add_user_to_group()

                Prompt.ask("\n按回车键继续...")

            except KeyboardInterrupt:
                console.print("\n[yellow]操作已取消[/yellow]")
                try:
                    if Prompt.ask("\n是否返回主菜单？", choices=["y", "n"], default="y") == "n":
                        console.print("[yellow]感谢使用，再见！[/yellow]")
                        return
                except KeyboardInterrupt:
                    console.print("\n[yellow]感谢使用，再见！[/yellow]")
                    return

        except KeyboardInterrupt:
            console.print("\n[yellow]感谢使用，再见！[/yellow]")
            break

if __name__ == "__main__":
    try:
        main_menu()
    except Exception as e:
        console.print(f"\n[red]发生错误：{str(e)}[/red]")
        sys.exit(1) 