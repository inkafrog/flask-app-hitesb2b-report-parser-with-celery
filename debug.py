from src.bot.hitesb2b import HitesB2b

driver = HitesB2b()
driver.login('Rigoberto.Sepulveda@aocchile.cl', 'envision0520')
one = driver.download_first_file()
two = driver.download_second()

breakpoint()
