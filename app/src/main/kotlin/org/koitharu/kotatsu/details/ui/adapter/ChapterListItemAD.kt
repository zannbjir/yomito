package org.koitharu.kotatsu.details.ui.adapter

import android.graphics.Typeface
import androidx.core.content.ContextCompat
import androidx.core.view.isVisible
import com.hannesdorfmann.adapterdelegates4.dsl.adapterDelegateViewBinding
import org.koitharu.kotatsu.R
import org.koitharu.kotatsu.core.ui.list.AdapterDelegateClickListenerAdapter
import org.koitharu.kotatsu.core.ui.list.OnListItemClickListener
import org.koitharu.kotatsu.core.util.ext.drawableStart
import org.koitharu.kotatsu.core.util.ext.getThemeColor
import org.koitharu.kotatsu.core.util.ext.getThemeColorStateList
import org.koitharu.kotatsu.core.util.ext.getThemeResId
import org.koitharu.kotatsu.core.util.ext.textAndVisible
import org.koitharu.kotatsu.databinding.ItemChapterBinding
import org.koitharu.kotatsu.details.ui.model.ChapterListItem
import org.koitharu.kotatsu.list.ui.model.ListModel
import com.google.android.material.R as materialR

fun chapterListItemAD(
	clickListener: OnListItemClickListener<ChapterListItem>,
) = adapterDelegateViewBinding<ChapterListItem, ListModel, ItemChapterBinding>(
	viewBinding = { inflater, parent -> ItemChapterBinding.inflate(inflater, parent, false) },
	on = { item, _, _ -> item is ChapterListItem && !item.isGrid },
) {

	AdapterDelegateClickListenerAdapter(this, clickListener).attach(itemView)
	val isExpressive = context.getThemeResId(R.attr.detailsChapterListItemStyle, 0) ==
		R.style.Widget_Kotatsu_Details_ChapterCard_Expressive
	val titleTypeface = binding.textViewTitle.typeface
	val descriptionTypeface = binding.textViewDescription.typeface

	bind {
		binding.textViewTitle.text = item.getTitle(context.resources)
		binding.textViewDescription.textAndVisible = item.description
		if (isExpressive) {
			val containerAttr: Int
			val contentAttr: Int
			val supportingAttr: Int
			when {
				item.isCurrent -> {
					containerAttr = materialR.attr.colorPrimaryContainer
					contentAttr = materialR.attr.colorOnPrimaryContainer
					supportingAttr = materialR.attr.colorOnPrimaryContainer
				}

				item.isUnread && item.isNew -> {
					containerAttr = materialR.attr.colorSecondaryContainer
					contentAttr = materialR.attr.colorOnSecondaryContainer
					supportingAttr = materialR.attr.colorOnSecondaryContainer
				}

				item.isUnread -> {
					containerAttr = materialR.attr.colorSurfaceContainer
					contentAttr = materialR.attr.colorOnSurface
					supportingAttr = materialR.attr.colorOnSurfaceVariant
				}

				else -> {
					containerAttr = materialR.attr.colorSurfaceContainerLow
					contentAttr = materialR.attr.colorOnSurfaceVariant
					supportingAttr = materialR.attr.colorOnSurfaceVariant
				}
			}
			binding.root.setCardBackgroundColor(context.getThemeColor(containerAttr))
			binding.textViewTitle.setTextColor(context.getThemeColor(contentAttr))
			binding.textViewDescription.setTextColor(context.getThemeColor(supportingAttr))
			binding.textViewTitle.setTypeface(
				titleTypeface,
				if (item.isCurrent || item.isNew) Typeface.BOLD else Typeface.NORMAL,
			)
			binding.textViewDescription.setTypeface(
				descriptionTypeface,
				if (item.isCurrent) Typeface.BOLD else Typeface.NORMAL,
			)
			binding.textViewTitle.drawableStart = null
			binding.imageViewNew.isVisible = item.isUnread && item.isNew
		} else {
			binding.root.setCardBackgroundColor(android.graphics.Color.TRANSPARENT)
			when {
				item.isCurrent -> {
					binding.textViewTitle.drawableStart =
						ContextCompat.getDrawable(context, R.drawable.ic_current_chapter)
					binding.textViewTitle.setTextColor(
						context.getThemeColorStateList(android.R.attr.textColorPrimary),
					)
					binding.textViewDescription.setTextColor(
						context.getThemeColorStateList(android.R.attr.textColorPrimary),
					)
					binding.textViewTitle.setTypeface(titleTypeface, Typeface.BOLD)
					binding.textViewDescription.setTypeface(descriptionTypeface, Typeface.BOLD)
				}

				item.isUnread -> {
					binding.textViewTitle.drawableStart = if (item.isNew) {
						ContextCompat.getDrawable(context, R.drawable.ic_new)
					} else {
						null
					}
					binding.textViewTitle.setTextColor(
						context.getThemeColorStateList(android.R.attr.textColorPrimary),
					)
					binding.textViewDescription.setTextColor(
						context.getThemeColorStateList(materialR.attr.colorOutline),
					)
					binding.textViewTitle.setTypeface(titleTypeface, Typeface.NORMAL)
					binding.textViewDescription.setTypeface(descriptionTypeface, Typeface.NORMAL)
				}

				else -> {
					binding.textViewTitle.drawableStart = null
					binding.textViewTitle.setTextColor(
						context.getThemeColorStateList(android.R.attr.textColorHint),
					)
					binding.textViewDescription.setTextColor(
						context.getThemeColorStateList(android.R.attr.textColorHint),
					)
					binding.textViewTitle.setTypeface(titleTypeface, Typeface.NORMAL)
					binding.textViewDescription.setTypeface(descriptionTypeface, Typeface.NORMAL)
				}
			}
			binding.imageViewNew.isVisible = false
		}
		binding.imageViewBookmarked.isVisible = item.isBookmarked
		binding.imageViewDownloaded.isVisible = item.isDownloaded
	}
}
