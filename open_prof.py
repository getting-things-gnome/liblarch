import pstats
p = pstats.Stats('gtg.prof')
p.strip_dirs().sort_stats("cumulative").print_stats(20)
p.strip_dirs().sort_stats("time").print_stats(20)
p.strip_dirs().sort_stats("name").print_stats(20)
p.print_callers('update_task')
