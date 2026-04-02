#!/usr/bin/env python3
"""Test the clean_input function"""

import sys, tty, termios

def clean_input(prompt=""):
    """
    Proper text input with backspace, delete, and arrow keys.
    """
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    
    buf = []    # Characters before cursor
    after = []  # Characters after cursor (for right-arrow)
    
    sys.stdout.write(prompt)
    sys.stdout.flush()
    
    def redraw():
        """Redraw the entire line from cursor position"""
        # Move to start of input
        if buf:
            sys.stdout.write(f'\x1b[{len(buf)}D')
        # Clear everything after prompt
        total = len(buf) + len(after)
        sys.stdout.write(' ' * total)
        # Move back to start
        sys.stdout.write(f'\x1b[{total}D')
        # Write all characters
        sys.stdout.write(''.join(buf))
        if after:
            sys.stdout.write(''.join(reversed(after)))
            # Move cursor back to correct position
            sys.stdout.write(f'\x1b[{len(after)}D')
        sys.stdout.flush()
    
    try:
        tty.setraw(fd)
        
        while True:
            ch = sys.stdin.read(1)
            
            # Enter
            if ch in ('\r', '\n'):
                sys.stdout.write('\r\n')
                sys.stdout.flush()
                return ''.join(buf + list(reversed(after)))
            
            # CTRL+C
            if ch == '\x03':
                sys.stdout.write('\r\n')
                sys.stdout.flush()
                raise KeyboardInterrupt
            
            # CTRL+D
            if ch == '\x04':
                sys.stdout.write('\r\n')
                sys.stdout.flush()
                raise EOFError
            
            # Escape sequence
            if ch == '\x1b':
                seq = sys.stdin.read(2)
                if seq == '[D':  # Left arrow
                    if buf:
                        after.append(buf.pop())
                        sys.stdout.write('\x1b[D')
                        sys.stdout.flush()
                elif seq == '[C':  # Right arrow
                    if after:
                        buf.append(after.pop())
                        sys.stdout.write('\x1b[C')
                        sys.stdout.flush()
                elif seq == '[3':  # Possible delete key
                    tilde = sys.stdin.read(1)  # Should be '~'
                    if tilde == '~' and after:  # Delete key
                        after.pop()
                        # Redraw from current position
                        if after:
                            sys.stdout.write(''.join(reversed(after)))
                            sys.stdout.write(' ')
                            sys.stdout.write(f'\x1b[{len(after) + 1}D')
                        else:
                            sys.stdout.write(' \x1b[D')
                        sys.stdout.flush()
                elif seq == '[H':  # Home
                    if buf:
                        sys.stdout.write(f'\x1b[{len(buf)}D')
                        after = list(reversed(buf)) + after
                        buf = []
                        sys.stdout.flush()
                elif seq == '[F':  # End
                    if after:
                        sys.stdout.write(f'\x1b[{len(after)}C')
                        buf = buf + list(reversed(after))
                        after = []
                        sys.stdout.flush()
                # Ignore other escape sequences
                continue
            
            # Backspace
            if ch in ('\x7f', '\b'):
                if buf:
                    buf.pop()
                    sys.stdout.write('\b \b')  # Move back, clear, move back
                    if after:
                        # Redraw characters after cursor
                        sys.stdout.write(''.join(reversed(after)))
                        sys.stdout.write(' ')
                        sys.stdout.write(f'\x1b[{len(after) + 1}D')
                    sys.stdout.flush()
                continue
            
            # CTRL+U - clear line
            if ch == '\x15':
                total = len(buf) + len(after)
                if total > 0:
                    sys.stdout.write(f'\x1b[{total}D')
                    sys.stdout.write(' ' * total)
                    sys.stdout.write(f'\x1b[{total}D')
                    buf = []
                    after = []
                    sys.stdout.flush()
                continue
            
            # CTRL+A - beginning
            if ch == '\x01':
                if buf:
                    sys.stdout.write(f'\x1b[{len(buf)}D')
                    after = list(reversed(buf)) + after
                    buf = []
                    sys.stdout.flush()
                continue
            
            # CTRL+E - end
            if ch == '\x05':
                if after:
                    sys.stdout.write(f'\x1b[{len(after)}C')
                    buf = buf + list(reversed(after))
                    after = []
                    sys.stdout.flush()
                continue
            
            # Regular printable character
            if ord(ch) >= 32:
                buf.append(ch)
                if after:
                    # Insert in middle
                    sys.stdout.write(ch)
                    sys.stdout.write(''.join(reversed(after)))
                    sys.stdout.write(f'\x1b[{len(after)}D')
                else:
                    sys.stdout.write(ch)
                sys.stdout.flush()
    
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)


# Test
if __name__ == "__main__":
    print("Test: Type 'hello', backspace twice, type 'p', press Enter")
    print("Expected output: 'help'")
    print()
    result = clean_input("> ")
    print(f"You typed: '{result}'")
    print()
    if result == "help":
        print("PASS")
    else:
        print(f"FAIL - expected 'help', got '{result}'")
