#!/bin/bash


cd "$(dirname "$0")"

PLUGIN=aaaby1
URL="plugin://plugin.video.$PLUGIN/"
ID=2

url="$URL"


hist=()

while : ; do

	menu=()
	[[ $url = *'?'* ]] || url="$url?"
	hist+=( "$url" )

	echo "-----  Call '$url'  -----"
	while read line; do
		case "$line" in
			ITEM·*) menu+=( "$line" );;
			*)      echo $line;;
		esac
	done < <(python main.py --fake "${url%%\?*}" "$ID" "?${url#*\?}" "resume:false")

	while : ; do

		echo "[36mURL:[0m $url"
		echo "[93m0:[0m <-- go back"
		if [[ ${#menu[@]} != 0 ]]; then
			urls=()
			i=1
			for line in "${menu[@]}"; do
				IFS=· read op title url _ <<< "$line"
				# echo " --$op--$title--$url"
				case "$op" in
					ITEM)  echo "[93m$i:[0m $title"; urls+=( "$url" );;
				esac
				let i++
			done
		fi
		echo "[93mQ:[0m --- quit"

		read -r -p "Select: " ans || exit
		# echo "ans: '$ans'"
		case "$ans" in
			0)
				url="${hist[-2]}"
				unset 'hist[-1]'
				unset 'hist[-1]'
				break
				;;
			[1-9]|[1-9][0-9]|[1-9][0-9][0-9])
				let ans--
				if [[ $ans -lt ${#urls[@]} ]]; then
					url="${urls[$ans]}"
					break
				fi
				;;
			exit|quit|q|Q)
				exit
				;;
			*)
				;;
		esac
	done
done
