package org.koitharu.kotatsu.details.ui.adapter

import android.content.res.ColorStateList
import android.graphics.Typeface
import androidx.core.view.isVisible
import com.hannesdorfmann.adapterdelegates4.dsl.adapterDelegateViewBinding
import org.koitharu.kotatsu.R
import org.koitharu.kotatsu.core.ui.list.AdapterDelegateClickListenerAdapter
import org.koitharu.kotatsu.core.ui.list.OnListItemClickListener
import org.koitharu.kotatsu.core.util.ext.getThemeColorStateList
import org.koitharu.kotatsu.core.util.ext.getThemeColor
import org.koitharu.kotatsu.core.util.ext.getThemeResId
import org.koitharu.kotatsu.core.util.ext.setTooltipCompat
import org.koitharu.kotatsu.databinding.ItemChapterGridBinding
import org.koitharu.kotatsu.details.ui.model.ChapterListItem
import org.koitharu.kotatsu.list.ui.model.ListModel
import androidx.appcompat.R as appcompatR
import com.google.android.material.R as materialR

fun chapterGridItemAD(
	clickListener: OnListItemClickListener<ChapterListItem>,
) = adapterDelegateViewBinding<ChapterListItem, ListModel, ItemChapterGridBinding>(
	viewBinding = { inflater, parent -> ItemChapterGridBinding.inflate(inflater, parent, false) },
	on = { item, _, _ -> item is ChapterListItem && item.isGrid },
) {

	AdapterDelegateClickListenerAdapter(this, clickListener).attach(itemView)
	val isExpressive = context.getThemeResId(R.attr.detailsChapterGridItemStyle, 0) ==
		R.style.Widget_Kotatsu_Details_ChapterGridCard_Expressive
	val titleTypeface = binding.textViewTitle.typeface

	bind { payloads ->
		if (payloads.isEmpty()) {
			binding.textViewTitle.text = item.chapter.numberString() ?: "?"
			itemView.setTooltipCompat(item.chapter.title)
		}
		binding.imageViewNew.isVisible = item.isNew
		binding.imageViewCurrent.isVisible = item.isCurrent
		binding.imageViewBookmarked.isVisible = item.isBookmarked
		binding.imageViewDownloaded.isVisible = item.isDownloaded

		if (isExpressive) {
			val containerAttr: Int
			val contentAttr: Int
			when {
				item.isCurrent -> {
					containerAttr = materialR.attr.colorPrimaryContainer
					contentAttr = materialR.attr.colorOnPrimaryContainer
				}

				item.isUnread && item.isNew -> {
					containerAttr = materialR.attr.colorSecondaryContainer
					contentAttr = materialR.attr.colorOnSecondaryContainer
				}

				item.isUnread -> {
					containerAttr = materialR.attr.colorSurfaceContainer
					contentAttr = materialR.attr.colorOnSurface
				}

				else -> {
					containerAttr = materialR.attr.colorSurfaceContainerLow
					contentAttr = materialR.attr.colorOnSurfaceVariant
				}
			}
			val contentColor = context.getThemeColor(contentAttr)
			binding.root.setCardBackgroundColor(context.getThemeColor(containerAttr))
			binding.textViewTitle.setTextColor(contentColor)
			binding.textViewTitle.setTypeface(
				titleTypeface,
				if (item.isCurrent || item.isNew) Typeface.BOLD else Typeface.NORMAL,
			)
			val tint = ColorStateList.valueOf(contentColor)
			binding.imageViewCurrent.imageTintList = tint
			binding.imageViewBookmarked.imageTintList = tint
			binding.imageViewDownloaded.imageTintList = tint
			binding.imageViewNew.imageTintList = ColorStateList.valueOf(
				context.getThemeColor(appcompatR.attr.colorError),
			)
		} else when {
			item.isCurrent -> {
				binding.textViewTitle.setTextColor(context.getThemeColorStateList(android.R.attr.textColorPrimary))
				binding.textViewTitle.setTypeface(titleTypeface, Typeface.BOLD)
			}

			item.isUnread -> {
				binding.textViewTitle.setTextColor(context.getThemeColorStateList(android.R.attr.textColorPrimary))
				binding.textViewTitle.setTypeface(titleTypeface, Typeface.NORMAL)
			}

			else -> {
				binding.textViewTitle.setTextColor(context.getThemeColorStateList(android.R.attr.textColorHint))
				binding.textViewTitle.setTypeface(titleTypeface, Typeface.NORMAL)
			}
		}
	}
}

