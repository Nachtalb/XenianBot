Indirect Commands:\n
~~~~~~~~~~~~~~~~~~\n
\n
% for group_name, command_list in indirect_commands.items():
    <%
        title_line = '^' * len(group_name)
    %>
    ${group_name}\n
    ${title_line}\n
    \n
    % for command in command_list:
        -\ \ **${command['title']}** - ${command['description']}\n
    % endfor
    \n
% endfor


BE SURE TO REPLACE "\ \ " with 2 whitespaces
